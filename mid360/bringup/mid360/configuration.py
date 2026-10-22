"""Device-only MID360 configuration and Livox SDK network settings."""

from collections.abc import Mapping
import ipaddress
import math
from pathlib import Path

import yaml


DEFAULT_CONFIG = {
    'enabled': True,
    'model': 'Mid360s',
    'ip': '192.168.1.120',
    'host_ip': '192.168.1.5',
    'frame_id': 'livox_frame',
    'publish_freq': 10.0,
    'xfer_format': 0,
}


def normalize_config(values=None):
    """Merge a partial device mapping with defaults and validate local values."""
    if values is None:
        values = {}
    if not isinstance(values, Mapping):
        raise ValueError('MID360 configuration must be a YAML mapping.')
    unknown = set(values) - set(DEFAULT_CONFIG)
    if unknown:
        raise ValueError(f'Unknown MID360 configuration fields: {sorted(unknown, key=str)}')
    config = {**DEFAULT_CONFIG, **values}
    if not isinstance(config['enabled'], bool):
        raise ValueError('mid360.enabled must be a boolean.')
    if config['model'] not in ('MID360', 'Mid360s'):
        raise ValueError('mid360.model must be MID360 or Mid360s.')
    for field in ('ip', 'host_ip'):
        value = config[field]
        try:
            if not isinstance(value, str):
                raise ipaddress.AddressValueError()
            ipaddress.IPv4Address(value)
        except ipaddress.AddressValueError as exc:
            raise ValueError(f'mid360.{field} must be an IPv4 address.') from exc
    frame = config['frame_id']
    if not isinstance(frame, str) or not frame or any(c.isspace() for c in frame):
        raise ValueError('mid360.frame_id must be a nonempty frame name without whitespace.')
    frequency = config['publish_freq']
    if (isinstance(frequency, bool) or not isinstance(frequency, (float, int))
            or not math.isfinite(frequency) or frequency <= 0):
        raise ValueError('mid360.publish_freq must be a positive finite number.')
    transfer = config['xfer_format']
    if isinstance(transfer, bool) or not isinstance(transfer, int) or transfer not in (0, 1):
        raise ValueError('mid360.xfer_format must be 0 (PointCloud2) or 1 (CustomMsg).')
    return config


def load_config(path):
    """Load a standalone device YAML, independently of robot configuration."""
    values = yaml.safe_load(Path(path).read_text())
    if not isinstance(values, Mapping):
        raise ValueError('MID360 configuration must be a YAML mapping.')
    return normalize_config(values)


def lidar_config(values=None):
    """Generate SDK JSON with zero extrinsics; mounting calibration belongs in TF."""
    lidar = normalize_config(values)
    return {
        'lidar_summary_info': {'lidar_type': 8},
        lidar['model']: {
            'lidar_net_info': {
                'cmd_data_port': 56100, 'push_msg_port': 56200,
                'point_data_port': 56300, 'imu_data_port': 56400,
                'log_data_port': 56500,
            },
            # Explicit mapping opens host sockets before discovery, including
            # when the robot and the MID360 use different LAN interfaces.
            'host_net_info': [{
                'lidar_ip': [lidar['ip']], 'host_ip': lidar['host_ip'],
                'cmd_data_port': 56101, 'push_msg_port': 56201,
                'point_data_port': 56301, 'imu_data_port': 56401,
                'log_data_port': 56501,
            }],
        },
        'lidar_configs': [{
            'ip': lidar['ip'], 'pcl_data_type': 1, 'pattern_mode': 0,
            'extrinsic_parameter': {
                'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0,
                'x': 0, 'y': 0, 'z': 0,
            },
        }],
    }
