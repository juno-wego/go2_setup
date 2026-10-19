"""Driver includes must isolate arguments while preserving the DDS environment."""

import importlib.util
from pathlib import Path

from launch import LaunchContext, LaunchDescription
from launch.actions import (
    DeclareLaunchArgument, OpaqueFunction, SetEnvironmentVariable,
    SetLaunchConfiguration,
)
from launch.launch_description_source import LaunchDescriptionSource
from launch.utilities import visit_all_entities_and_collect_futures
import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def bringup(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT))
    spec = importlib.util.spec_from_file_location(
        'wego_bringup_launch_for_tests', ROOT / 'launch/bringup.launch.py'
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    'arguments, defaults',
    [
        pytest.param(
            {
                'network_interface': 'go2',
                'params_file': '/driver/go2.yaml',
                'enable_control': 'false',
                'enable_bridge': 'true',
                'enable_description': 'true',
                'rviz': 'false',
                'use_sim_time': 'false',
            },
            {},
            id='go2',
        ),
        pytest.param(
            {
                'camera_namespace': 'camera',
                'camera_name': 'd435i',
                'enable_color': 'true',
                'enable_depth': 'true',
                'depth_module.depth_profile': '480x270x15',
                'serial_no': '_262422072409',
            },
            {'config_file': ''},
            id='realsense',
        ),
    ],
)
def test_driver_arguments_and_dds_environment_are_scoped(
    bringup, monkeypatch, tmp_path, arguments, defaults
):
    # Create the context before global launch actions change its environment.
    # forwarding=False would incorrectly reset these changes to this baseline.
    monkeypatch.setenv('ROS_DOMAIN_ID', '1')
    monkeypatch.setenv('RMW_IMPLEMENTATION', 'rmw_fastrtps_cpp')
    monkeypatch.setenv('CYCLONEDDS_URI', '<CycloneDDS/>')
    context = LaunchContext()
    dds_environment = {
        'ROS_DOMAIN_ID': '37',
        'RMW_IMPLEMENTATION': 'rmw_cyclonedds_cpp',
        'CYCLONEDDS_URI': (
            '<CycloneDDS><Domain><General><Interfaces>'
            '<NetworkInterface name="go2"/>'
            '</Interfaces></General></Domain></CycloneDDS>'
        ),
    }
    for name, value in dds_environment.items():
        SetEnvironmentVariable(name, value).execute(context)

    # This parent file must never become the RealSense driver's config_file.
    robot_yaml = tmp_path / 'robot.yaml'
    robot_yaml.write_text(yaml.safe_dump({
        'tf': {'mid360': {'xyz': None, 'rpy': None}},
    }))
    parent_arguments = {
        'config_file': str(robot_yaml),
        'network_interface': 'parent-interface',
        'params_file': '/parent/go2.yaml',
        'enable_control': 'parent-control-value',
        'enable_bridge': 'parent-bridge-value',
        'enable_description': 'parent-description-value',
        'description_file': '/parent/robot.urdf',
        'rviz': 'true',
    }
    context.launch_configurations.update(parent_arguments)
    parent_environment = dict(context.environment)
    observations = []

    def observe_driver(driver_context):
        observations.append(dict(driver_context.launch_configurations))
        assert observations[-1] == {**arguments, **defaults}
        for name, value in dds_environment.items():
            assert driver_context.environment[name] == value
        return []

    # An in-memory source exercises the real include and group actions, without
    # constructing or launching ROS nodes or loading hardware driver launches.
    driver_source = LaunchDescriptionSource(LaunchDescription([
        *[DeclareLaunchArgument(name) for name in arguments],
        *[
            DeclareLaunchArgument(name, default_value=value)
            for name, value in defaults.items()
        ],
        OpaqueFunction(function=observe_driver),
        SetLaunchConfiguration('config_file', 'child-only.yaml'),
        SetLaunchConfiguration('driver_private', 'child-only'),
        SetEnvironmentVariable('ROS_DOMAIN_ID', '96'),
    ]))
    group = bringup._driver_launch(driver_source, arguments)
    futures = visit_all_entities_and_collect_futures(group, context)

    assert futures == []
    assert observations == [{**arguments, **defaults}]
    assert context.launch_configurations == parent_arguments
    assert dict(context.environment) == parent_environment
    assert yaml.safe_load(robot_yaml.read_text())['tf']['mid360']['xyz'] is None
