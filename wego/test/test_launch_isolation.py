"""Driver includes must isolate arguments while preserving the DDS environment."""

import importlib.util
from pathlib import Path

from launch import LaunchContext, LaunchDescription
from launch.actions import (
    DeclareLaunchArgument, LogInfo, OpaqueFunction, SetEnvironmentVariable,
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
        'wego_launch_for_tests', ROOT / 'launch/bringup.launch.py'
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_go2_launch_receives_only_its_device_settings(bringup, monkeypatch, tmp_path):
    config = yaml.safe_load((ROOT / 'config/robot.yaml').read_text())
    assert 'enable_control' not in config['go2']
    config['go2']['network_interface'] = 'lo'
    config['lidar']['enabled'] = config['camera']['enabled'] = False
    config['tf']['publish_mounts'] = False
    path = tmp_path / 'robot.yaml'
    path.write_text(yaml.safe_dump(config))
    monkeypatch.setattr(bringup, 'get_package_share_directory', lambda package: str(tmp_path / package))
    included = []

    def include_driver(source, arguments):
        included.append(arguments)
        return LogInfo(msg='Driver include captured for inspection')

    monkeypatch.setattr(bringup, '_driver_launch', include_driver)
    context = LaunchContext()
    context.launch_configurations.update(config_file=str(path), rviz='false')
    bringup._setup(context)

    assert len(included) == 1
    settings = yaml.safe_load(Path(included[0]['config_file']).read_text())
    assert settings == {key: value for key, value in config['go2'].items()
                        if key != 'enabled'}
    assert included[0]['rviz'] == 'false'
    assert included[0]['description_file'] == ''
    declared = [action for action in bringup.generate_launch_description().entities
                if isinstance(action, DeclareLaunchArgument)]
    assert {action.name for action in declared} == {'config_file', 'rviz'}


def test_sensor_only_system_does_not_require_go2_or_change_dds(
    bringup, monkeypatch, tmp_path,
):
    path = tmp_path / 'camera-only.yaml'
    path.write_text(yaml.safe_dump({'camera': {'enabled': True, 'serial_no': '123456'}}))
    requested = []

    def share(package):
        requested.append(package)
        assert package in ('wego', 'd435i')
        return str(tmp_path / package)

    monkeypatch.setattr(bringup, 'get_package_share_directory', share)
    included = []
    monkeypatch.setattr(bringup, '_driver_launch',
                        lambda source, arguments: included.append(arguments) or LogInfo(msg='captured'))
    context = LaunchContext()
    context.launch_configurations.update(config_file=str(path), rviz='false')
    actions = bringup._setup(context)

    assert requested == ['wego', 'd435i']
    assert len(included) == 1
    assert yaml.safe_load(Path(included[0]['config_file']).read_text())['serial_no'] == '123456'
    assert not any(isinstance(action, SetEnvironmentVariable) for action in actions)


def test_aggregate_dispatches_three_packages_with_independent_config_files(
    bringup, monkeypatch, tmp_path,
):
    config = yaml.safe_load((ROOT / 'config/robot.yaml').read_text())
    config['go2']['network_interface'] = 'lo'
    config['go2']['domain_id'] = 37
    config['tf']['publish_mounts'] = False
    path = tmp_path / 'system.yaml'
    path.write_text(yaml.safe_dump(config))
    requested = []

    def share(package):
        requested.append(package)
        assert package in ('wego', 'go2', 'mid360', 'd435i')
        return str(tmp_path / package)

    monkeypatch.setattr(bringup, 'get_package_share_directory', share)
    included = []
    monkeypatch.setattr(bringup, '_driver_launch',
                        lambda source, arguments: included.append(arguments) or LogInfo(msg='captured'))
    context = LaunchContext()
    context.launch_configurations.update(config_file=str(path), rviz='false')
    actions = bringup._setup(context)

    assert requested == ['wego', 'go2', 'mid360', 'd435i']
    assert len(included) == 3
    for section, arguments in zip(('go2', 'lidar', 'camera'), included):
        settings = yaml.safe_load(Path(arguments['config_file']).read_text())
        assert settings == {key: value for key, value in config[section].items()
                            if key != 'enabled'}
    for action in actions:
        if isinstance(action, SetEnvironmentVariable):
            action.execute(context)
    assert context.environment['ROS_DOMAIN_ID'] == '37'
    assert context.environment['RMW_IMPLEMENTATION'] == 'rmw_cyclonedds_cpp'
    assert 'name="lo"' in context.environment['CYCLONEDDS_URI']


@pytest.mark.parametrize(
    'arguments, defaults',
    [
        pytest.param(
            {
                'network_interface': 'go2',
                'params_file': '/driver/go2.yaml',
                'enable_control': 'true',
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
