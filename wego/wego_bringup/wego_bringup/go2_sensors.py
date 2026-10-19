"""Expose Go2 native sensors alongside the unchanged Unitree DDS topics."""

from array import array
import time

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import CompressedImage, Image, Imu, PointCloud2
from unitree_api.msg import Request, Response
from unitree_go.msg import LidarState, LowState, UwbState, WirelessController


class Go2Sensors(Node):
    def __init__(self):
        super().__init__('go2_sensors')
        sensor_qos = QoSProfile(depth=1, reliability=ReliabilityPolicy.BEST_EFFORT)
        self._sensor_qos = sensor_qos
        self._relays = []
        for message_type, source, target in (
            (PointCloud2, '/utlidar/cloud', '/go2/lidar'),
            (Imu, '/utlidar/imu', '/go2/lidar/imu'),
            (LidarState, '/utlidar/lidar_state', '/go2/lidar/state'),
            (LowState, '/lowstate', '/go2/low_state'),
            (WirelessController, '/wirelesscontroller', '/go2/wireless_controller'),
            (UwbState, '/uwbstate', '/go2/uwb_state'),
        ):
            publisher = self.create_publisher(message_type, target, sensor_qos)
            self._relays.append({
                'publisher': publisher, 'type': message_type,
                'source': source, 'subscription': None,
            })
        self._relay_timer = self.create_timer(0.2, self._update_relays)

        self._image_pub = self.create_publisher(
            Image, '/go2/camera/image_raw', sensor_qos)
        self._compressed_pub = self.create_publisher(
            CompressedImage, '/go2/camera/image_raw/compressed', sensor_qos)
        self._request_pub = self.create_publisher(Request, '/api/videohub/request', 10)
        self._response_sub = self.create_subscription(
            Response, '/api/videohub/response', self._on_image, sensor_qos)
        self._pending_id = None
        self._requested_at = 0.0
        self._last_warning = float('-inf')
        self._timer = self.create_timer(0.2, self._request_image)

    def _update_relays(self):
        # Native topics remain directly accessible. Subscribe to duplicate
        # aliases only while a reader needs them, especially the 500 Hz state.
        for relay in self._relays:
            publisher = relay['publisher']
            if publisher.get_subscription_count() > 0:
                if relay['subscription'] is None:
                    relay['subscription'] = self.create_subscription(
                        relay['type'], relay['source'], publisher.publish, self._sensor_qos)
            elif relay['subscription'] is not None:
                self.destroy_subscription(relay['subscription'])
                relay['subscription'] = None

    def _warn(self, message):
        now = time.monotonic()
        if now - self._last_warning >= 10.0:
            self.get_logger().warning(message)
            self._last_warning = now

    def _request_image(self):
        now = time.monotonic()
        if self._pending_id is not None:
            if now - self._requested_at < 2.0:
                return
            self._warn('Go2 camera image request timed out; retrying.')
        if self._request_pub.get_subscription_count() == 0:
            return
        request = Request()
        request.header.identity.id = time.monotonic_ns()
        request.header.identity.api_id = 1001
        self._pending_id = request.header.identity.id
        self._requested_at = now
        self._request_pub.publish(request)

    def _on_image(self, response):
        if (response.header.identity.id != self._pending_id
                or response.header.identity.api_id != 1001):
            return
        self._pending_id = None
        if response.header.status.code != 0:
            self._warn(f'Go2 camera returned status {response.header.status.code}.')
            return
        # Unitree Response.binary is int8[], whereas JPEG bytes are unsigned.
        data = response.binary.tobytes()
        if not data:
            self._warn('Go2 camera returned an empty image.')
            return
        try:
            image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
        except cv2.error:
            image = None
        if image is None:
            self._warn('Go2 camera returned an invalid JPEG image.')
            return
        stamp = self.get_clock().now().to_msg()
        compressed = CompressedImage()
        compressed.header.stamp = stamp
        compressed.header.frame_id = 'front_camera'
        compressed.format = 'bgr8; jpeg compressed bgr8'
        # Pass arrays directly to ROS setters to avoid per-byte Python checks
        # on the full-resolution image buffers.
        compressed.data = array('B', data)
        self._compressed_pub.publish(compressed)
        if self._image_pub.get_subscription_count() == 0:
            return
        raw = Image()
        raw.header = compressed.header
        raw.height, raw.width = image.shape[:2]
        raw.encoding = 'bgr8'
        raw.step = raw.width * 3
        raw.data = array('B', image.tobytes())
        self._image_pub.publish(raw)


def main(args=None):
    rclpy.init(args=args)
    node = Go2Sensors()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
