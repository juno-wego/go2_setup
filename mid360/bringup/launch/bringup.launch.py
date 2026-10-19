import json
from pathlib import Path
import shutil
import tempfile

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, RegisterEventHandler
from launch.event_handlers import OnShutdown
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from mid360.configuration import lidar_config, load_config


def _cleanup(context, folder):
    shutil.rmtree(folder, ignore_errors=True)
    return []


def _setup(context):
    config = load_config(LaunchConfiguration('config_file').perform(context))
    if not config['enabled']:
        return []
    folder = tempfile.mkdtemp(prefix='mid360-')
    path = Path(folder) / 'MID360_config.json'
    try:
        path.write_text(json.dumps(lidar_config(config), indent=2))
    except Exception:
        shutil.rmtree(folder, ignore_errors=True)
        raise
    return [
        RegisterEventHandler(OnShutdown(on_shutdown=[
            OpaqueFunction(function=_cleanup, kwargs={'folder': folder}),
        ])),
        Node(
            package='livox_ros_driver2', executable='livox_ros_driver2_node',
            name='livox_lidar_publisher', output='screen',
            parameters=[{
                'user_config_path': str(path), 'frame_id': config['frame_id'],
                'xfer_format': config['xfer_format'], 'multi_topic': 0,
                'data_src': 0, 'publish_freq': float(config['publish_freq']),
                'output_data_type': 0, 'cmdline_input_bd_code': 'livox0000000001',
            }],
        ),
    ]


def generate_launch_description():
    share = Path(get_package_share_directory('mid360'))
    return LaunchDescription([
        DeclareLaunchArgument('config_file', default_value=str(share / 'config/device.yaml')),
        OpaqueFunction(function=_setup),
    ])
