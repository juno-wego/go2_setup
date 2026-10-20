"""Go2 validation is device-local and does not require an installed NIC."""

from copy import deepcopy
import errno
import struct
from xml.etree import ElementTree

import pytest
import yaml

from go2.configuration import DEFAULT_CONFIG, dds_environment, load_config, normalize_config
from go2 import configuration


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


@pytest.fixture
def interface_probe(monkeypatch):
    """Supply kernel interface responses without touching network configuration."""
    monkeypatch.setattr(configuration.Path, 'exists', lambda path: True)
    calls = []

    class Probe:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def fileno(self):
            return 42

    monkeypatch.setattr(configuration.socket, 'socket', lambda *args: Probe())

    def configure(*, flags=0x1, ipv4=True, error=None):
        def ioctl(descriptor, operation, request):
            assert descriptor == 42
            assert request.split(b'\0', 1)[0] in (b'go2', b'lo')
            calls.append(operation)
            if error is not None:
                raise error
            if operation == 0x8913:
                return b'\0' * 16 + struct.pack('H', flags) + b'\0' * 22
            assert operation == 0x8915
            if not ipv4:
                raise OSError(errno.EADDRNOTAVAIL, 'Cannot assign requested address')
            return b'\0' * 40
        monkeypatch.setattr(configuration.fcntl, 'ioctl', ioctl)
        return calls

    return configure


def test_auto_interface_does_not_probe_the_host(monkeypatch):
    def unexpected_probe(*args, **kwargs):
        pytest.fail('Automatic interface selection must not probe a NIC')

    monkeypatch.setattr(configuration.Path, 'exists', unexpected_probe)
    monkeypatch.setattr(configuration.socket, 'socket', unexpected_probe)
    configuration.validate_interface(normalize_config({'network_interface': ''}))


def test_missing_interface_is_rejected_before_opening_socket(monkeypatch):
    monkeypatch.setattr(configuration.Path, 'exists', lambda path: False)
    monkeypatch.setattr(configuration.socket, 'socket',
                        lambda *args: pytest.fail('Missing NIC must not open a socket'))
    with pytest.raises(ValueError, match="'go2' does not exist"):
        configuration.validate_interface(DEFAULT_CONFIG)


def test_down_interface_is_rejected_with_network_recovery_hint(interface_probe):
    calls = interface_probe(flags=0, ipv4=True)
    with pytest.raises(ValueError, match='administratively DOWN') as error:
        configuration.validate_interface(DEFAULT_CONFIG)
    assert calls == [0x8913]
    assert 'host network profile and static IPv4 configuration' in str(error.value)


def test_up_interface_without_ipv4_is_rejected_before_dds_start(interface_probe):
    interface_probe(flags=0x1, ipv4=False)
    with pytest.raises(ValueError, match='has no IPv4 address') as error:
        configuration.validate_interface(DEFAULT_CONFIG)
    assert 'CycloneDDS cannot use it' in str(error.value)
    assert 'network profile' in str(error.value)


@pytest.mark.parametrize('interface,flags', [
    ('go2', 0x1),  # IFF_UP alone: carrier/IFF_RUNNING is not required.
    ('lo', 0x49),  # IFF_UP | IFF_LOOPBACK | IFF_RUNNING; operstate is UNKNOWN.
])
def test_up_ipv4_interface_is_accepted_without_carrier_or_operstate_probe(
    interface_probe, interface, flags,
):
    calls = interface_probe(flags=flags, ipv4=True)
    configuration.validate_interface(normalize_config({'network_interface': interface}))
    assert calls == [0x8913, 0x8915]


def test_interface_probe_failure_has_actionable_error(interface_probe):
    interface_probe(error=OSError(errno.ENODEV, 'No such device'))
    with pytest.raises(ValueError, match="Cannot inspect network interface 'go2'") as error:
        configuration.validate_interface(DEFAULT_CONFIG)
    assert 'network profile' in str(error.value)
