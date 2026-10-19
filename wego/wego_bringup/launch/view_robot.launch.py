"""Inspect the Go2 URDF using virtual joint states on a loopback ROS domain."""

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import LogInfo, SetEnvironmentVariable
from launch_ros.actions import Node

from wego_bringup.configuration import load_config, active_mounts
from wego_bringup.robot_description import mounted_description
from wego_bringup.visualization import rviz_actions


def generate_launch_description():
    share = Path(get_package_share_directory('wego_bringup'))
    go2_share = Path(get_package_share_directory('go2_description'))
    description = (go2_share / 'urdf/go2_description.urdf').read_text()
    config = load_config(share / 'config/robot.yaml')
    description = mounted_description(description, active_mounts(config))
    config['go2']['enabled'] = True
    config['lidar']['enabled'] = config['camera']['enabled'] = False
    actions = [
        SetEnvironmentVariable('RMW_IMPLEMENTATION', 'rmw_cyclonedds_cpp'),
        SetEnvironmentVariable('ROS_DOMAIN_ID', '92'),
        SetEnvironmentVariable('CYCLONEDDS_URI',
            '<CycloneDDS><Domain><General><Interfaces>'
            '<NetworkInterface name="lo"/>'
            '</Interfaces></General></Domain></CycloneDDS>'),
        LogInfo(msg='Go2 URDF preview: virtual joint states, loopback ROS domain 92.'),
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             name='robot_state_publisher', output='screen',
             parameters=[{'robot_description': description, 'use_sim_time': False}]),
        Node(package='joint_state_publisher', executable='joint_state_publisher',
             name='wego_preview_joint_states', output='screen',
             parameters=[{'robot_description': description}]),
    ]
    actions.extend(rviz_actions(config, share / 'rviz', urdf_only=True))
    return LaunchDescription(actions)
