"""Check generated RViz views using the package's real templates."""

import copy
import importlib.util
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def visualization():
    spec = importlib.util.spec_from_file_location(
        'wego_visualization_for_tests', ROOT / 'wego_bringup/visualization.py'
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def config():
    settings = yaml.safe_load((ROOT / 'config/robot.yaml').read_text())
    settings['go2']['enabled'] = True
    settings['lidar'].update(enabled=True, xfer_format=0)
    settings['camera'].update(enabled=True, pointcloud=False)
    settings['tf'].update(publish_mounts=False)
    return settings


@pytest.fixture
def render(visualization, config, tmp_path):
    def generate(*, urdf_only=False):
        original = copy.deepcopy(config)
        paths = visualization.write_rviz_configs(
            config, ROOT / 'rviz', tmp_path, urdf_only=urdf_only
        )
        assert config == original, 'Rendering must leave the input config unchanged.'
        return {
            name: yaml.safe_load(path.read_text())
            for name, path in paths.items()
        }

    return generate


def displays(view):
    return {
        display['Name']: display
        for display in view['Visualization Manager']['Displays']
    }


def assert_enabled(display, expected):
    assert display['Enabled'] is expected
    assert display['Value'] is expected


def test_uncalibrated_sensors_use_independent_frames_and_configured_topics(config, render):
    config['camera'].update(namespace='/perception/front/', name='d435i', pointcloud=True)
    config['lidar']['frame_id'] = 'mid360_sensor'

    views = render()

    assert set(views) == {'robot', 'lidar'}
    assert views['robot']['Visualization Manager']['Global Options']['Fixed Frame'] == 'base_link'
    assert views['lidar']['Visualization Manager']['Global Options']['Fixed Frame'] == 'mid360_sensor'
    robot = displays(views['robot'])
    assert_enabled(robot['MID360 Cloud'], False)
    assert_enabled(robot['D435i Cloud'], False)
    assert_enabled(robot['D435i RGB'], True)
    assert_enabled(robot['D435i Depth'], True)
    assert robot['D435i RGB']['Topic']['Value'] == '/perception/front/d435i/color/image_raw'
    assert robot['D435i Depth']['Topic']['Value'] == '/perception/front/d435i/depth/image_rect_raw'
    assert robot['D435i Cloud']['Topic']['Value'] == '/perception/front/d435i/depth/color/points'
    cloud = displays(views['lidar'])['MID360 Cloud']
    assert_enabled(cloud, True)
    assert cloud['Topic']['Value'] == '/livox/lidar'


def test_calibrated_mounts_put_clouds_in_robot_view_without_duplicate_lidar(config, render):
    config['tf'].update(publish_mounts=True)
    # Synthetic measurements make this a complete calibrated test configuration.
    for sensor in ('mid360', 'd435i'):
        config['tf'][sensor].update(enabled=True, status='measured',
                                    xyz=[0.1, 0.2, 0.3], rpy=[0.0, 0.0, 0.0])
    config['camera']['pointcloud'] = True

    views = render()

    assert set(views) == {'robot'}
    robot = displays(views['robot'])
    assert_enabled(robot['MID360 Cloud'], True)
    assert_enabled(robot['D435i Cloud'], True)
    assert views['robot']['Visualization Manager']['Global Options']['Fixed Frame'] == 'base_link'


def test_reference_lidar_mount_combines_only_the_lidar_cloud(config, render):
    config['tf']['publish_mounts'] = True
    config['camera']['pointcloud'] = True

    views = render()

    assert set(views) == {'robot'}
    robot = displays(views['robot'])
    assert_enabled(robot['MID360 Cloud'], True)
    assert_enabled(robot['D435i Cloud'], False)
    assert_enabled(robot['D435i RGB'], True)


def test_lidar_reference_does_not_connect_to_an_unmounted_camera_without_go2(config, render):
    config['go2']['enabled'] = False
    config['tf']['publish_mounts'] = True

    views = render()

    assert set(views) == {'robot', 'lidar'}
    assert views['robot']['Visualization Manager']['Global Options']['Fixed Frame'] == 'camera_link'
    assert_enabled(displays(views['robot'])['MID360 Cloud'], False)


def test_urdf_only_contains_robot_tf_and_grid_even_when_sensors_are_enabled(config, render):
    config['go2']['enabled'] = False
    config['camera']['pointcloud'] = True

    views = render(urdf_only=True)

    assert set(views) == {'robot'}
    robot = displays(views['robot'])
    assert set(robot) == {'Go2 Robot', 'TF', 'Grid'}
    assert {display['Class'] for display in robot.values()} == {
        'rviz_default_plugins/RobotModel',
        'rviz_default_plugins/TF',
        'rviz_default_plugins/Grid',
    }
    for display in robot.values():
        assert_enabled(display, True)
    assert views['robot']['Visualization Manager']['Global Options']['Fixed Frame'] == 'base_link'


def test_custom_livox_messages_do_not_enable_pointcloud2_or_lidar_preview(config, render):
    config['lidar']['xfer_format'] = 1

    views = render()

    assert set(views) == {'robot'}
    robot = displays(views['robot'])
    assert_enabled(robot['MID360 Cloud'], False)
    assert all(
        display['Class'] != 'rviz_default_plugins/PointCloud2'
        for display in robot.values() if display['Enabled']
    )
    assert_enabled(robot['D435i RGB'], True)
    assert_enabled(robot['D435i Depth'], True)
