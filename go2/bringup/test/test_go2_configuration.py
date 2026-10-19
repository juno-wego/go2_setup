"""Go2 validation is device-local and does not require an installed NIC."""

from copy import deepcopy
from xml.etree import ElementTree

import pytest
import yaml

from go2.configuration import DEFAULT_CONFIG, dds_environment, load_config, normalize_config


def test_defaults_are_independent_and_enabled_is_aggregate_only():
    defaults = deepcopy(DEFAULT_CONFIG)
    result = normalize_config({'enabled': False, 'network_interface': ' absent-nic '})
    assert result == {**defaults, 'network_interface': 'absent-nic'}
    result['domain_id'] = 17
    assert DEFAULT_CONFIG == defaults


@pytest.mark.parametrize('values', [
    [], {'robot_ip': 'not-an-ip'}, {'robot_ip': 1},
    {'domain_id': True}, {'domain_id': -1}, {'domain_id': 233},
    {'domain_id': 1.5}, {'network_interface': None},
    {'network_interface': '../go2'}, {'unknown_setting': True},
])
def test_invalid_device_settings_are_rejected(values):
    with pytest.raises(ValueError):
        normalize_config(values)


def test_device_yaml_is_not_an_aggregate_robot_yaml(tmp_path):
    path = tmp_path / 'device.yaml'
    path.write_text(yaml.safe_dump({'network_interface': 'lo', 'domain_id': 37}))
    assert load_config(path) == {**DEFAULT_CONFIG, 'network_interface': 'lo', 'domain_id': 37}
    path.write_text(yaml.safe_dump({'go2': {'network_interface': 'lo'}}))
    with pytest.raises(ValueError):
        load_config(path)


def test_dds_environment_keeps_domain_and_escapes_interface():
    config = normalize_config({'network_interface': 'a&b"c', 'domain_id': 37})
    environment = dds_environment(config)
    assert environment['RMW_IMPLEMENTATION'] == 'rmw_cyclonedds_cpp'
    assert environment['ROS_DOMAIN_ID'] == '37'
    tree = ElementTree.fromstring(environment['CYCLONEDDS_URI'])
    assert tree.find('.//NetworkInterface').get('name') == 'a&b"c'
    assert 'CYCLONEDDS_URI' not in dds_environment(normalize_config({'network_interface': ''}))
