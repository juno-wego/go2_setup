"""Inspect Go2 composition without starting drivers or ROS nodes."""

import importlib.util
from pathlib import Path

import pytest
import yaml

pytest.importorskip('launch')
pytest.importorskip('launch_ros')
from launch import LaunchContext, LaunchDescription
from launch.actions import (
    DeclareLaunchArgument, LogInfo, OpaqueFunction, SetEnvironmentVariable,
    SetLaunchConfiguration,
)
from launch.launch_description_source import LaunchDescriptionSource
from launch.utilities import visit_all_entities_and_collect_futures


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def bringup():
    spec = importlib.util.spec_from_file_location('go2_launch_for_tests', ROOT / 'launch/bringup.launch.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_device_launch_keeps_existing_control_behavior_and_dds_scope(bringup, monkeypatch, tmp_path):
    path = tmp_path / 'go2.yaml'
    path.write_text(yaml.safe_dump({'network_interface': 'lo', 'domain_id': 37}))
    monkeypatch.setattr(bringup, 'get_package_share_directory', lambda package: str(tmp_path / package))
    included, sensors = [], []

    def capture_driver(source, arguments):
        included.append(arguments)
        return LogInfo(msg='Captured upstream driver')

    def capture_sensor(**kwargs):
        sensors.append(kwargs)
        return OpaqueFunction(function=lambda context: observe_environment(context))

    def observe_environment(context):
        assert context.environment['RMW_IMPLEMENTATION'] == 'rmw_cyclonedds_cpp'
        assert context.environment['ROS_DOMAIN_ID'] == '37'
        assert 'name="lo"' in context.environment['CYCLONEDDS_URI']
        return []

    monkeypatch.setattr(bringup, '_driver_launch', capture_driver)
    monkeypatch.setattr(bringup, 'Node', capture_sensor)
    context = LaunchContext()
    context.launch_configurations.update(config_file=str(path), description_file='', rviz='false')
    environment_before = dict(context.environment)
    group, = bringup._setup(context)
    assert visit_all_entities_and_collect_futures(group, context) == []
    assert dict(context.environment) == environment_before
    assert len(included) == 1
    assert included[0]['enable_control'] == 'true'
    assert included[0]['enable_bridge'] == included[0]['enable_description'] == 'true'
    assert included[0]['params_file'] == str(tmp_path / 'go2/config/go2.yaml')
    assert included[0]['description_file'] == str(tmp_path / 'go2_description/urdf/go2_description.urdf')
    assert sensors[0]['package'] == 'go2'
    assert sensors[0]['executable'] == 'go2_sensors'
    declared = [action for action in bringup.generate_launch_description().entities
                if isinstance(action, DeclareLaunchArgument)]
    assert {action.name for action in declared} == {'config_file', 'description_file', 'rviz'}


def test_upstream_arguments_are_isolated_and_dds_environment_is_preserved(bringup):
    context = LaunchContext()
    context.launch_configurations.update(config_file='/parent/robot.yaml', rviz='true')
    SetEnvironmentVariable('ROS_DOMAIN_ID', '37').execute(context)
    before_arguments = dict(context.launch_configurations)
    before_environment = dict(context.environment)
    arguments = {'params_file': '/go2/config/go2.yaml', 'enable_control': 'true'}
    observations = []

    def observe(child):
        observations.append(dict(child.launch_configurations))
        assert child.environment['ROS_DOMAIN_ID'] == '37'
        return []

    source = LaunchDescriptionSource(LaunchDescription([
        *[DeclareLaunchArgument(name) for name in arguments],
        OpaqueFunction(function=observe),
        SetLaunchConfiguration('private_driver_arg', 'value'),
        SetEnvironmentVariable('ROS_DOMAIN_ID', '96'),
    ]))
    group = bringup._driver_launch(source, arguments)
    assert visit_all_entities_and_collect_futures(group, context) == []
    assert observations == [arguments]
    assert context.launch_configurations == before_arguments
    assert dict(context.environment) == before_environment


def test_enabled_device_validates_interface_without_starting_nodes(bringup, monkeypatch, tmp_path):
    path = tmp_path / 'go2.yaml'
    path.write_text('network_interface: this-nic-cannot-exist\n')
    monkeypatch.setattr(bringup, 'get_package_share_directory', lambda package: str(tmp_path / package))
    context = LaunchContext()
    context.launch_configurations.update(config_file=str(path), description_file='', rviz='false')
    with pytest.raises(ValueError, match='Network interface'):
        bringup._setup(context)
