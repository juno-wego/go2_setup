from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument, GroupAction, IncludeLaunchDescription,
    OpaqueFunction, ResetLaunchConfigurations,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import SetParameter

from d435i.configuration import load_config


def _setup(context):
    config = load_config(LaunchConfiguration('config_file').perform(context))
    if not config['enabled']:
        return []
    share = Path(get_package_share_directory('realsense2_camera'))
    arguments = {
        'camera_namespace': config['namespace'], 'camera_name': config['name'],
        'enable_color': 'true', 'enable_depth': 'true',
        'depth_module.depth_profile': config['depth_profile'],
        'rgb_camera.color_profile': config['color_profile'],
        'enable_gyro': str(config['enable_imu']).lower(),
        'enable_accel': str(config['enable_imu']).lower(),
        'unite_imu_method': '2', 'publish_tf': 'true',
        # Start from a clean USB device state after previous camera sessions.
        'initial_reset': 'true',
        'pointcloud.enable': str(config['pointcloud']).lower(),
        'align_depth.enable': 'true', 'enable_sync': 'true',
    }
    if config['serial_no']:
        # The underscore preserves the serial as a string in upstream YAML parsing.
        arguments['serial_no'] = '_' + config['serial_no'].lstrip('_')
    return [GroupAction(actions=[
        # Keep the surrounding process environment, isolating driver launch args
        # such as config_file from any parent robot configuration.
        ResetLaunchConfigurations(),
        # Librealsense 2.58 on this Jetson names its accelerated filter
        # "Pointcloud (NEON)". Keep it in sync with the standard pointcloud
        # launch option, scoped to this camera rather than other drivers.
        SetParameter(name='pointcloud__neon_.enable', value=config['pointcloud']),
        SetParameter(name='pointcloud__neon_.stream_filter', value=2),
        SetParameter(name='pointcloud__neon_.stream_index_filter', value=0),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(share / 'launch/rs_launch.py')),
            launch_arguments=arguments.items(),
        ),
    ])]


def generate_launch_description():
    share = Path(get_package_share_directory('d435i'))
    return LaunchDescription([
        DeclareLaunchArgument('config_file', default_value=str(share / 'config/device.yaml')),
        OpaqueFunction(function=_setup),
    ])
