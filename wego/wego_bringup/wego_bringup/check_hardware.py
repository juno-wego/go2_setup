"""Observe hardware and ROS topics without publishing robot commands."""

import argparse
import json
import subprocess
import time

import rclpy
from rclpy.qos import qos_profile_sensor_data
from rosidl_runtime_py.utilities import get_message


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--duration', type=float, default=10.0)
    args = parser.parse_args()
    print(subprocess.check_output(['ip', '-br', 'addr'], text=True))
    print(subprocess.check_output(['lsusb'], text=True))
    rclpy.init()
    node = rclpy.create_node('wego_hardware_check')
    wanted = {
        '/lowstate', '/lf/sportmodestate', '/go2/odom', '/go2/imu',
        '/joint_states', '/livox/lidar', '/livox/imu',
        '/camera/camera/color/image_raw', '/camera/camera/depth/image_rect_raw',
        '/camera/camera/imu',
    }
    received = {}
    subscriptions = {}

    def callback(topic, msg):
        state = received.setdefault(topic, {'messages': 0})
        state['messages'] += 1
        if hasattr(msg, 'header'):
            state['frame_id'] = msg.header.frame_id

    end = time.monotonic() + args.duration
    while time.monotonic() < end:
        for topic, types in node.get_topic_names_and_types():
            if topic in wanted and topic not in subscriptions:
                try:
                    subscriptions[topic] = node.create_subscription(
                        get_message(types[0]), topic,
                        lambda msg, t=topic: callback(t, msg), qos_profile_sensor_data,
                    )
                except (ImportError, AttributeError, ValueError) as exc:
                    received[topic] = {'error': str(exc)}
        rclpy.spin_once(node, timeout_sec=0.1)
    print(json.dumps({
        'observed_topics': received,
        'topics_without_samples': sorted(wanted - received.keys()),
        'nodes': node.get_node_names(),
    }, indent=2))
    node.destroy_node()
    rclpy.shutdown()
