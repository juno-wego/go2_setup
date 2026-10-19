import json
import os
import shutil
import tempfile
from pathlib import Path
from xml.sax.saxutils import quoteattr

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument, GroupAction, IncludeLaunchDescription, LogInfo,
    OpaqueFunction, RegisterEventHandler, ResetLaunchConfigurations, SetEnvironmentVariable,
)
from launch.event_handlers import OnShutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from wego_bringup.configuration import load_config, lidar_config, active_mounts
from wego_bringup.robot_description import mounted_description
from wego_bringup.visualization import rviz_actions


def _cleanup(context, folder):
    shutil.rmtree(folder, ignore_errors=True)
    return []


def _driver_launch(source, arguments):
    # Keep the DDS environment, but isolate driver arguments such as config_file.
    return GroupAction(actions=[
        ResetLaunchConfigurations(),
        IncludeLaunchDescription(source, launch_arguments=arguments.items()),
    ])


def _setup(context):
    share = Path(get_package_share_directory('wego_bringup'))
    config = load_config(LaunchConfiguration('config_file').perform(context))
    interface = config['go2']['network_interface']
    if interface and not (Path('/sys/class/net') / interface).exists():
        raise ValueError(f'Network interface {interface!r} does not exist. '
                         'Set go2.network_interface in the robot configuration.')
    actions = [
        SetEnvironmentVariable('RMW_IMPLEMENTATION', 'rmw_cyclonedds_cpp'),
        SetEnvironmentVariable('ROS_DOMAIN_ID', str(config['go2']['domain_id'])),
    ]
    if interface:
        actions.append(SetEnvironmentVariable(
            'CYCLONEDDS_URI',
            '<CycloneDDS><Domain><General><Interfaces>'
            f'<NetworkInterface name={quoteattr(interface)} '
            'priority="default" multicast="default" />'
            '</Interfaces></General></Domain></CycloneDDS>',
        ))

    mounts = active_mounts(config)

    if config['go2']['enabled']:
        go2_share = Path(get_package_share_directory('go2_base'))
        description_share = Path(get_package_share_directory('go2_description'))
        description = description_share / 'urdf/go2_description.urdf'
        if mounts:
            folder = tempfile.mkdtemp(prefix='wego-description-')
            mounted_path = Path(folder) / 'go2_sensors.urdf'
            mounted_path.write_text(mounted_description(description.read_text(), mounts))
            description = mounted_path
            actions.append(RegisterEventHandler(OnShutdown(on_shutdown=[
                OpaqueFunction(function=_cleanup, kwargs={'folder': folder})
            ])))
        actions.append(_driver_launch(
            PythonLaunchDescriptionSource(str(go2_share / 'launch/go2_bringup.launch.py')),
            {
                'network_interface': interface,
                'params_file': str(share / 'config/go2.yaml'),
                'description_file': str(description),
                'enable_control': 'true',
                'enable_bridge': 'true', 'enable_description': 'true',
                'rviz': 'false',
                'use_sim_time': 'false',
            },
        ))

    if config['lidar']['enabled']:
        folder = tempfile.mkdtemp(prefix='wego-mid360-')
        path = Path(folder) / 'MID360_config.json'
        path.write_text(json.dumps(lidar_config(config), indent=2))
        actions.append(RegisterEventHandler(OnShutdown(on_shutdown=[
            OpaqueFunction(function=_cleanup, kwargs={'folder': folder})
        ])))
        lidar = config['lidar']
        actions.append(Node(
            package='livox_ros_driver2', executable='livox_ros_driver2_node',
            name='livox_lidar_publisher', output='screen',
            parameters=[{
                'user_config_path': str(path), 'frame_id': lidar['frame_id'],
                'xfer_format': int(lidar['xfer_format']), 'multi_topic': 0,
                'data_src': 0, 'publish_freq': float(lidar['publish_freq']),
                'output_data_type': 0, 'cmdline_input_bd_code': 'livox0000000001',
            }],
        ))

    if config['camera']['enabled']:
        camera = config['camera']
        rs_share = Path(get_package_share_directory('realsense2_camera'))
        args = {
            'camera_namespace': camera['namespace'], 'camera_name': camera['name'],
            'enable_color': 'true', 'enable_depth': 'true',
            'depth_module.depth_profile': camera['depth_profile'],
            'rgb_camera.color_profile': camera['color_profile'],
            'enable_gyro': str(camera['enable_imu']).lower(),
            'enable_accel': str(camera['enable_imu']).lower(),
            'unite_imu_method': '2', 'publish_tf': 'true',
            'pointcloud.enable': str(camera['pointcloud']).lower(),
            'align_depth.enable': 'true', 'enable_sync': 'true',
        }
        if camera['serial_no']:
            args['serial_no'] = '_' + str(camera['serial_no']).lstrip('_')
        actions.append(_driver_launch(
            PythonLaunchDescriptionSource(str(rs_share / 'launch/rs_launch.py')), args,
        ))

    for key, mount in mounts.items():
        actions.append(LogInfo(msg=(
            f'{key} mount: {mount["parent"]} -> {mount["child"]}; '
            f'status={mount["status"]}, yaw_verified={mount.get("yaw_verified", False)}'
        )))
        if not config['go2']['enabled']:
            # With Go2 enabled the composite URDF owns this fixed joint.
            # Publishing the same child from a second TF source is avoided.
            x, y, z = mount['xyz']
            roll, pitch, yaw = mount['rpy']
            actions.append(Node(
                package='tf2_ros', executable='static_transform_publisher',
                name=key + '_mount_tf', output='screen',
                arguments=[
                    '--x', str(x), '--y', str(y), '--z', str(z),
                    '--roll', str(roll), '--pitch', str(pitch), '--yaw', str(yaw),
                    '--frame-id', mount['parent'], '--child-frame-id', mount['child'],
                ],
            ))
    if not mounts:
        actions.append(LogInfo(msg=(
            'No sensor mounting TF is enabled for this launch. '
            'Go2 TF and RealSense internal TF remain available.'
        )))
    rviz = LaunchConfiguration('rviz').perform(context).lower().strip()
    if rviz not in ('true', 'false', '1', '0'):
        raise ValueError('rviz must be true or false.')
    if rviz in ('true', '1'):
        actions.extend(rviz_actions(config, share / 'rviz'))
    return actions


def generate_launch_description():
    share = Path(get_package_share_directory('wego_bringup'))
    return LaunchDescription([
        DeclareLaunchArgument('config_file', default_value=str(share / 'config/robot.yaml')),
        DeclareLaunchArgument('rviz', default_value='true'),
        OpaqueFunction(function=_setup),
    ])
