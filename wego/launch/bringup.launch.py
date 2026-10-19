"""Compose independent device packages, mounting transforms and RViz."""

import shutil
import tempfile
from pathlib import Path

import yaml
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

from go2.configuration import dds_environment, validate_interface
from wego.configuration import active_mounts, load_config
from wego.robot_description import mounted_description
from wego.visualization import rviz_actions


DEVICES = (('go2', 'go2'), ('lidar', 'mid360'), ('camera', 'd435i'))


def _cleanup(context, folder):
    shutil.rmtree(folder, ignore_errors=True)
    return []


def _driver_launch(source, arguments):
    # Share the system DDS environment, while keeping device arguments local.
    return GroupAction(actions=[
        ResetLaunchConfigurations(),
        IncludeLaunchDescription(source, launch_arguments=arguments.items()),
    ])


def _setup(context):
    share = Path(get_package_share_directory('wego'))
    config = load_config(LaunchConfiguration('config_file').perform(context))
    rviz = LaunchConfiguration('rviz').perform(context).lower().strip()
    if rviz not in ('true', 'false', '1', '0'):
        raise ValueError('rviz must be true or false.')
    actions = []
    if config['go2']['enabled']:
        validate_interface(config['go2'])
        # Sensors and RViz must share Go2's domain and DDS interface in this
        # system. Sensor-only launches retain the caller's DDS environment.
        actions.extend(SetEnvironmentVariable(name, value)
                       for name, value in dds_environment(config['go2']).items())
    mounts = active_mounts(config)
    folder = tempfile.mkdtemp(prefix='wego-bringup-')
    try:
        description = ''
        if config['go2']['enabled'] and mounts:
            model = (Path(get_package_share_directory('go2_description'))
                     / 'urdf/go2_description.urdf')
            path = Path(folder) / 'robot.urdf'
            path.write_text(mounted_description(model.read_text(), mounts))
            description = str(path)
        for section, package in DEVICES:
            if not config[section]['enabled']:
                continue
            # Each package receives only its device settings. In particular,
            # the aggregate config_file cannot leak into the RealSense launch.
            path = Path(folder) / f'{package}.yaml'
            settings = {key: value for key, value in config[section].items()
                        if key != 'enabled'}
            path.write_text(yaml.safe_dump(settings))
            arguments = {'config_file': str(path)}
            if package == 'go2':
                arguments.update(description_file=description, rviz='false')
            source = (Path(get_package_share_directory(package))
                      / 'launch/bringup.launch.py')
            actions.append(_driver_launch(
                PythonLaunchDescriptionSource(str(source)), arguments,
            ))
        actions.insert(0, RegisterEventHandler(OnShutdown(on_shutdown=[
            OpaqueFunction(function=_cleanup, kwargs={'folder': folder}),
        ])))
    except Exception:
        shutil.rmtree(folder, ignore_errors=True)
        raise

    for key, mount in mounts.items():
        actions.append(LogInfo(msg=(
            f'{key} mount: {mount["parent"]} -> {mount["child"]}; '
            f'status={mount["status"]}, yaw_verified={mount.get("yaw_verified", False)}'
        )))
        if not config['go2']['enabled']:
            # With Go2 enabled the composed URDF owns this fixed joint.
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
            'Device internal transforms remain available.'
        )))
    if rviz in ('true', '1'):
        actions.extend(rviz_actions(config, share / 'rviz'))
    return actions


def generate_launch_description():
    share = Path(get_package_share_directory('wego'))
    return LaunchDescription([
        DeclareLaunchArgument('config_file', default_value=str(share / 'config/robot.yaml')),
        DeclareLaunchArgument('rviz', default_value='true'),
        OpaqueFunction(function=_setup),
    ])
