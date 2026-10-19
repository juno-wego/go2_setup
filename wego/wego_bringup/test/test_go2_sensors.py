"""Check video RPC isolation, image decoding and retries without hardware."""

from array import array
import time

import pytest

rclpy = pytest.importorskip('rclpy')
pytest.importorskip('unitree_api.msg')
pytest.importorskip('unitree_go.msg')
cv2 = pytest.importorskip('cv2')
import numpy as np

from unitree_api.msg import Response
from wego_bringup.go2_sensors import Go2Sensors


class Publisher:
    def __init__(self, subscriptions=1):
        self.messages = []
        self.subscriptions = subscriptions

    def publish(self, msg):
        self.messages.append(msg)

    def get_subscription_count(self):
        return self.subscriptions


@pytest.fixture
def node(monkeypatch):
    monkeypatch.setenv('ROS_DOMAIN_ID', '92')
    monkeypatch.setenv('RMW_IMPLEMENTATION', 'rmw_cyclonedds_cpp')
    monkeypatch.setenv('CYCLONEDDS_URI', (
        '<CycloneDDS><Domain><General><Interfaces><NetworkInterface name="lo"/>'
        '</Interfaces></General></Domain></CycloneDDS>'))
    rclpy.init()
    sensor = Go2Sensors()
    sensor._image_pub = Publisher()
    sensor._compressed_pub = Publisher()
    sensor._request_pub = Publisher()
    yield sensor
    sensor.destroy_node()
    rclpy.shutdown()


def response(identity=42, api=1001, status=0, data=b''):
    msg = Response()
    msg.header.identity.id = identity
    msg.header.identity.api_id = api
    msg.header.status.code = status
    msg.binary = array('b', data)
    return msg


def test_camera_only_publishes_its_matching_successful_jpeg(node):
    node._pending_id = 42
    image = np.full((8, 12, 3), (25, 100, 240), dtype=np.uint8)
    ok, encoded = cv2.imencode('.jpg', image)
    assert ok
    jpeg = encoded.tobytes()

    node._on_image(response(identity=41, data=jpeg))
    node._on_image(response(api=1002, data=jpeg))
    assert not node._image_pub.messages
    assert node._pending_id == 42

    node._on_image(response(data=jpeg))

    assert node._pending_id is None
    raw, = node._image_pub.messages
    compressed, = node._compressed_pub.messages
    assert (raw.width, raw.height, raw.encoding, raw.step) == (12, 8, 'bgr8', 36)
    assert bytes(compressed.data) == jpeg
    assert bytes(raw.data) == cv2.imdecode(encoded, cv2.IMREAD_COLOR).tobytes()
    assert raw.header == compressed.header
    assert raw.header.frame_id == 'front_camera'


@pytest.mark.parametrize('status,data', [(3203, b''), (0, b''), (0, b'broken jpeg')])
def test_camera_failure_does_not_publish_and_allows_retry(node, status, data):
    node._pending_id = 42
    node._on_image(response(status=status, data=data))
    assert node._pending_id is None
    assert not node._image_pub.messages
    assert not node._compressed_pub.messages
    node._request_image()
    assert len(node._request_pub.messages) == 1


def test_camera_waits_for_a_server_and_limits_outstanding_requests(node):
    node._request_pub.subscriptions = 0
    node._request_image()
    assert node._pending_id is None
    assert not node._request_pub.messages
    node._request_pub.subscriptions = 1
    node._request_image()
    first, = node._request_pub.messages
    assert first.header.identity.api_id == 1001
    assert first.header.policy.noreply is False
    node._request_image()
    assert len(node._request_pub.messages) == 1
    node._requested_at = time.monotonic() - 3.0
    node._request_image()
    assert len(node._request_pub.messages) == 2
    assert node._pending_id != first.header.identity.id
    node._on_image(response(identity=first.header.identity.id))
    assert node._pending_id == node._request_pub.messages[-1].header.identity.id
