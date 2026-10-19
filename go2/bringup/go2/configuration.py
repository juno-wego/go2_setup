"""Device settings shared by standalone and aggregate Go2 launches."""

import ipaddress
from pathlib import Path
from xml.sax.saxutils import quoteattr

import yaml


DEFAULT_CONFIG = {
    'network_interface': 'go2',
    'robot_ip': '192.168.123.161',
    'domain_id': 0,
}


def normalize_config(values=None):
    """Merge defaults and validate Go2 settings without probing hardware."""
    if values is not None and not isinstance(values, dict):
        raise ValueError('Go2 configuration must be a YAML mapping.')
    config = {**DEFAULT_CONFIG, **(values or {})}
    # Enablement belongs to the aggregate launch, not the device itself.
    config.pop('enabled', None)
    unknown = set(config) - set(DEFAULT_CONFIG)
    if unknown:
        raise ValueError(f'Unknown Go2 configuration fields: {sorted(unknown)}')
    interface = config['network_interface']
    if not isinstance(interface, str):
        raise ValueError('go2.network_interface must be a string (empty means automatic).')
    config['network_interface'] = interface.strip()
    if '/' in interface or '\x00' in interface:
        raise ValueError('go2.network_interface must be a network interface name.')
    try:
        if not isinstance(config['robot_ip'], str):
            raise ipaddress.AddressValueError()
        ipaddress.IPv4Address(config['robot_ip'])
    except ipaddress.AddressValueError as exc:
        raise ValueError('go2.robot_ip must be an IPv4 address.') from exc
    domain = config['domain_id']
    if isinstance(domain, bool) or not isinstance(domain, int) or not 0 <= domain <= 232:
        raise ValueError('go2.domain_id must be an integer in 0..232.')
    return config


def load_config(path):
    """Read a YAML mapping containing only this device's settings."""
    values = yaml.safe_load(Path(path).read_text())
    if not isinstance(values, dict):
        raise ValueError('Go2 configuration must be a YAML mapping.')
    return normalize_config(values)


def validate_interface(config):
    """Check the selected NIC only when a caller actually enables Go2."""
    interface = config['network_interface']
    if interface and not (Path('/sys/class/net') / interface).exists():
        raise ValueError(f'Network interface {interface!r} does not exist. '
                         'Set network_interface in the Go2 configuration.')


def dds_environment(config):
    """DDS environment for Go2 and tools that exchange its ROS messages."""
    environment = {
        'RMW_IMPLEMENTATION': 'rmw_cyclonedds_cpp',
        'ROS_DOMAIN_ID': str(config['domain_id']),
    }
    interface = config['network_interface']
    if interface:
        environment['CYCLONEDDS_URI'] = (
            '<CycloneDDS><Domain><General><Interfaces>'
            f'<NetworkInterface name={quoteattr(interface)} '
            'priority="default" multicast="default" />'
            '</Interfaces></General></Domain></CycloneDDS>'
        )
    return environment
