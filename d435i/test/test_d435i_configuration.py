import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('d435i_configuration', ROOT / 'd435i/configuration.py')
configuration = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(configuration)


def test_standalone_defaults_do_not_pin_robot_serial():
    config = configuration.load_config(ROOT / 'config/device.yaml')
    assert config == configuration.DEFAULT_CONFIG
    assert config['serial_no'] == ''


def test_partial_device_settings_do_not_require_robot_mapping():
    values = {'serial_no': '262422072409', 'pointcloud': True}
    config = configuration.normalize_config(values)
    assert config['serial_no'] == values['serial_no']
    assert config['depth_profile'] == '480x270x15'
    assert values == {'serial_no': '262422072409', 'pointcloud': True}


@pytest.mark.parametrize('values,field', [
    ({'enabled': 'false'}, 'enabled'),
    ({'enable_imu': 1}, 'enable_imu'),
    ({'pointcloud': 'false'}, 'pointcloud'),
    ({'serial_no': 262422072409}, 'serial_no'),
    ({'serial_no': 'garbage'}, 'serial_no'),
    ({'depth_profile': '640x480x0'}, 'depth_profile'),
    ({'color_profile': '640x480'}, 'color_profile'),
    ({'name': ''}, 'name'),
    ({'namespace': 'robot/camera bad'}, 'namespace'),
])
def test_invalid_local_settings_are_rejected(values, field):
    with pytest.raises(ValueError, match=field):
        configuration.normalize_config(values)


def test_device_loader_rejects_whole_robot_and_nonmapping(tmp_path):
    path = tmp_path / 'device.yaml'
    path.write_text('go2: {}\n')
    with pytest.raises(ValueError, match='Unknown D435i'):
        configuration.load_config(path)
    path.write_text('[]\n')
    with pytest.raises(ValueError, match='mapping'):
        configuration.load_config(path)
