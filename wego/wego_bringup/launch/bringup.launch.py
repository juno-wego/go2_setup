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

from wego_bringup.configuration import load_config, lidar_config, validate_mounts
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
    for arg, section in (
        ('enable_go2', 'go2'), ('enable_lidar', 'lidar'), ('enable_camera', 'camera')
    ):
        override = LaunchConfiguration(arg).perform(context).lower().strip()
        if override:
            if override not in ('true', 'false'):
                raise ValueError(f'{arg} must be true or false.')
            config[section]['enabled'] = override == 'true'
    interface = LaunchConfiguration('network_interface').perform(context).strip()
    interface = interface or config['go2']['network_interface']
    if interface and not (Path('/sys/class/net') / interface).exists():
        raise ValueError(f'Network interface {interface!r} does not exist. '
                         'Set network_interface:=<Go2 LAN interface>.')
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

    if config['go2']['enabled']:
        go2_share = Path(get_package_share_directory('go2_base'))
        actions.append(_driver_launch(
            PythonLaunchDescriptionSource(str(go2_share / 'launch/go2_bringup.launch.py')),
            {
                'network_interface': interface,
                'params_file': str(share / 'config/go2.yaml'),
                'enable_control': str(config['go2']['enable_control']).lower(),
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

    if config['tf'].get('publish_mounts', False):
        validate_mounts(config['tf'])
        expected = {
            'mid360': config['lidar']['frame_id'],
            'd435i': config['camera']['name'] + '_link',
        }
        for key, section in (('mid360', 'lidar'), ('d435i', 'camera')):
            if not config[section]['enabled']:
                continue
            mount = config['tf'][key]
            if mount['child'] != expected[key]:
                raise ValueError(f'tf.{key}.child must match driver frame {expected[key]}.')
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
    else:
        actions.append(LogInfo(msg=(
            'Sensor mount TF is disabled until measured xyz/rpy are entered '
            'in robot.yaml. Go2 TF and RealSense internal TF remain available.'
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
        DeclareLaunchArgument('network_interface', default_value=''),
        DeclareLaunchArgument('enable_go2', default_value=''),
        DeclareLaunchArgument('enable_lidar', default_value=''),
        DeclareLaunchArgument('enable_camera', default_value=''),
        DeclareLaunchArgument('rviz', default_value='false'),
        OpaqueFunction(function=_setup),
    ])
