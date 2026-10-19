"""Device-only RealSense D435i configuration."""

from collections.abc import Mapping
from pathlib import Path
import re

import yaml


DEFAULT_CONFIG = {
    'enabled': True,
    'namespace': 'camera',
    'name': 'camera',
    'serial_no': '',
    'depth_profile': '480x270x15',
    'color_profile': '640x480x15',
    'enable_imu': True,
    'pointcloud': False,
}


def normalize_config(values=None):
    """Merge a partial device mapping with defaults and validate local values."""
    if values is None:
        values = {}
    if not isinstance(values, Mapping):
        raise ValueError('D435i configuration must be a YAML mapping.')
    unknown = set(values) - set(DEFAULT_CONFIG)
    if unknown:
        raise ValueError(f'Unknown D435i configuration fields: {sorted(unknown, key=str)}')
    config = {**DEFAULT_CONFIG, **values}
    for field in ('enabled', 'enable_imu', 'pointcloud'):
        if not isinstance(config[field], bool):
            raise ValueError(f'd435i.{field} must be a boolean.')
    name = config['name']
    if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', name):
        raise ValueError('d435i.name must be a valid ROS node name.')
    namespace = config['namespace']
    if not isinstance(namespace, str) or not re.fullmatch(
            r'(?:/?[A-Za-z_][A-Za-z0-9_]*(?:/[A-Za-z_][A-Za-z0-9_]*)*)?/?', namespace):
        raise ValueError('d435i.namespace must be a valid ROS namespace.')
    serial = config['serial_no']
    if not isinstance(serial, str) or (serial and not re.fullmatch(r'_?[0-9]+', serial)):
        raise ValueError('d435i.serial_no must be an empty string or a quoted serial number.')
    for field in ('depth_profile', 'color_profile'):
        profile = config[field]
        if (not isinstance(profile, str)
                or not re.fullmatch(r'[1-9][0-9]*x[1-9][0-9]*x[1-9][0-9]*', profile)):
            raise ValueError(f'd435i.{field} must be WIDTHxHEIGHTxFPS with positive integers.')
    return config


def load_config(path):
    """Load a standalone device YAML, independently of robot configuration."""
    values = yaml.safe_load(Path(path).read_text())
    if not isinstance(values, Mapping):
        raise ValueError('D435i configuration must be a YAML mapping.')
    return normalize_config(values)
