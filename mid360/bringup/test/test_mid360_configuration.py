import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('mid360_configuration', ROOT / 'mid360/configuration.py')
configuration = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(configuration)


def test_partial_device_settings_do_not_require_a_robot():
    values = {'ip': '192.168.2.177', 'host_ip': '192.168.2.5'}
    config = configuration.normalize_config(values)
    assert config['frame_id'] == 'livox_frame'
    assert values == {'ip': '192.168.2.177', 'host_ip': '192.168.2.5'}
    assert config['ip'] == values['ip']


@pytest.mark.parametrize('model', ['MID360', 'Mid360s'])
def test_sdk_json_keeps_sensor_coordinates_and_explicit_network_mapping(model):
    sdk = configuration.lidar_config({
        'model': model, 'ip': '192.168.2.177', 'host_ip': '192.168.2.5',
    })
    assert all(value == 0 for value in sdk['lidar_configs'][0]['extrinsic_parameter'].values())
    assert sdk['lidar_configs'][0]['ip'] == '192.168.2.177'
    assert sdk[model]['host_net_info'] == [{
        'lidar_ip': ['192.168.2.177'], 'host_ip': '192.168.2.5',
        'cmd_data_port': 56101, 'push_msg_port': 56201,
        'point_data_port': 56301, 'imu_data_port': 56401, 'log_data_port': 56501,
    }]


@pytest.mark.parametrize('values,field', [
    ({'ip': 'bad-ip'}, 'ip'),
    ({'host_ip': 12345}, 'host_ip'),
    ({'model': 'other'}, 'model'),
    ({'enabled': 'false'}, 'enabled'),
    ({'publish_freq': 0}, 'publish_freq'),
    ({'publish_freq': float('nan')}, 'publish_freq'),
    ({'xfer_format': True}, 'xfer_format'),
    ({'xfer_format': 2}, 'xfer_format'),
    ({'frame_id': ''}, 'frame_id'),
])
def test_invalid_local_settings_are_rejected(values, field):
    with pytest.raises(ValueError, match=field):
        configuration.normalize_config(values)


def test_device_yaml_and_partial_override(tmp_path):
    assert configuration.load_config(ROOT / 'config/device.yaml') == configuration.DEFAULT_CONFIG
    path = tmp_path / 'device.yaml'
    path.write_text('xfer_format: 1\n')
    assert configuration.load_config(path)['xfer_format'] == 1
    path.write_text('[]\n')
    with pytest.raises(ValueError, match='mapping'):
        configuration.load_config(path)
