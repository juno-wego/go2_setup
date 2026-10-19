"""Start the Go2 driver and native sensor adapters with local DDS settings."""

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument, GroupAction, IncludeLaunchDescription,
    OpaqueFunction, ResetLaunchConfigurations, SetEnvironmentVariable,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from go2.configuration import dds_environment, load_config, validate_interface


def _driver_launch(source, arguments):
    # Driver arguments are local; the scoped DDS environment is inherited.
    return GroupAction(actions=[
        ResetLaunchConfigurations(),
        IncludeLaunchDescription(source, launch_arguments=arguments.items()),
    ])


def _setup(context):
    share = Path(get_package_share_directory('go2'))
    config = load_config(LaunchConfiguration('config_file').perform(context))
    interface = config['network_interface']
    validate_interface(config)
    rviz = LaunchConfiguration('rviz').perform(context).strip().lower()
    if rviz not in ('true', 'false', '1', '0'):
        raise ValueError('rviz must be true or false.')
    description = LaunchConfiguration('description_file').perform(context).strip()
    if not description:
        description = str(Path(get_package_share_directory('go2_description'))
                          / 'urdf/go2_description.urdf')
    actions = [SetEnvironmentVariable(name, value)
               for name, value in dds_environment(config).items()]
    driver_share = Path(get_package_share_directory('go2_base'))
    actions.append(_driver_launch(
        PythonLaunchDescriptionSource(str(driver_share / 'launch/go2_bringup.launch.py')),
        {
            'network_interface': interface,
            'params_file': str(share / 'config/go2.yaml'),
            'description_file': description,
            'enable_control': 'true',
            'enable_bridge': 'true',
            'enable_description': 'true',
            'rviz': 'true' if rviz in ('true', '1') else 'false',
            'use_sim_time': 'false',
        },
    ))
    actions.append(Node(
        package='go2', executable='go2_sensors', name='go2_sensors', output='screen',
    ))
    # The DDS configuration applies to Go2 alone in a multi-device launch.
    return [GroupAction(actions=actions)]


def generate_launch_description():
    share = Path(get_package_share_directory('go2'))
    return LaunchDescription([
        DeclareLaunchArgument('config_file', default_value=str(share / 'config/device.yaml')),
        DeclareLaunchArgument('description_file', default_value=''),
        DeclareLaunchArgument('rviz', default_value='false'),
        OpaqueFunction(function=_setup),
    ])
