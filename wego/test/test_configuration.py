import copy
import importlib.util
from pathlib import Path

import pytest
import yaml
from mid360.configuration import lidar_config

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    'configuration', ROOT / 'wego/configuration.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_unknown_camera_mount_cannot_be_enabled(tmp_path):
    config = yaml.safe_load((ROOT / 'config/robot.yaml').read_text())
    config['tf']['d435i']['enabled'] = True
    path = tmp_path / 'robot.yaml'
    path.write_text(yaml.safe_dump(config))
    with pytest.raises(ValueError, match='measured'):
        module.load_config(path)


@pytest.mark.parametrize('model', ['MID360', 'Mid360s'])
def test_livox_mount_is_not_applied_twice(model):
    config = module.load_config(ROOT / 'config/robot.yaml')
    config['lidar']['model'] = model
    config['tf'].update(publish_mounts=True)
    for key in ('mid360', 'd435i'):
        config['tf'][key].update(enabled=True, status='measured',
                                 xyz=[0.31, 0.02, 0.19], rpy=[0.0, 0.2, 0.1])
    module.validate_mounts(config['tf'])
    lidar = lidar_config(config['lidar'])
    assert all(v == 0 for v in lidar['lidar_configs'][0]['extrinsic_parameter'].values())
    host = lidar[model]['host_net_info'][0]
    assert host['host_ip'] == config['lidar']['host_ip']
    assert host['lidar_ip'] == [config['lidar']['ip']]
    assert host['point_data_port'] == 56301
    assert host['imu_data_port'] == 56401


def test_duplicate_sensor_frame_is_rejected():
    config = module.load_config(ROOT / 'config/robot.yaml')
    tf = copy.deepcopy(config['tf'])
    tf.update(publish_mounts=True)
    for key in ('mid360', 'd435i'):
        tf[key].update(enabled=True, status='measured', xyz=[0.0, 0.0, 0.1],
                       rpy=[0.0, 0.0, 0.0], child='same_frame')
    with pytest.raises(ValueError, match='duplicate'):
        module.validate_mounts(tf)


def test_reference_mount_is_usable_without_claiming_verified_yaw():
    config = module.load_config(ROOT / 'config/robot.yaml')
    mounts = module.active_mounts(config)
    assert set(mounts) == {'mid360'}
    assert mounts['mid360']['parent'] == 'imu'
    assert mounts['mid360']['status'] == 'reference'
    assert mounts['mid360']['yaw_verified'] is False
    config['lidar']['enabled'] = False
    assert module.active_mounts(config) == {}


def test_reference_requires_provenance():
    config = module.load_config(ROOT / 'config/robot.yaml')
    config['tf']['mid360'].pop('source')
    with pytest.raises(ValueError, match='source'):
        module.validate_mounts(config['tf'])


def test_mount_cycle_is_rejected():
    config = module.load_config(ROOT / 'config/robot.yaml')
    config['tf']['d435i'].update(enabled=True, status='measured',
                                parent='livox_frame', xyz=[0, 0, 0], rpy=[0, 0, 0])
    config['tf']['mid360']['parent'] = 'camera_link'
    with pytest.raises(ValueError, match='cycle'):
        module.validate_mounts(config['tf'])


def test_camera_only_profile_needs_no_robot_or_lidar_settings(tmp_path):
    path = tmp_path / 'camera.yaml'
    path.write_text(yaml.safe_dump({'camera': {'enabled': True}}))
    config = module.load_config(path)
    assert config['camera']['enabled'] is True
    assert config['go2']['enabled'] is False
    assert config['lidar']['enabled'] is False
    assert module.active_mounts(config) == {}


def test_disabled_robot_settings_are_not_validated(tmp_path):
    path = tmp_path / 'sensor.yaml'
    path.write_text(yaml.safe_dump({
        'go2': {'enabled': False, 'robot_ip': 'not-connected', 'domain_id': -1},
        'lidar': {'enabled': True},
    }))
    config = module.load_config(path)
    assert config['lidar']['enabled'] is True
    assert config['go2']['enabled'] is False
