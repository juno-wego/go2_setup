"""Configuration shared by the launch file and hardware diagnostic."""

import ipaddress
import math
from pathlib import Path

import yaml


def load_config(path):
    config = yaml.safe_load(Path(path).read_text())
    if not isinstance(config, dict):
        raise ValueError('Robot configuration must be a YAML mapping.')
    for section in ('go2', 'lidar', 'camera', 'tf'):
        if not isinstance(config.get(section), dict):
            raise ValueError(f'Missing configuration section: {section}')
    domain = config['go2'].get('domain_id', 0)
    if isinstance(domain, bool) or not isinstance(domain, int) or not 0 <= domain <= 232:
        raise ValueError('go2.domain_id must be an integer in 0..232.')
    for field, value in (
        ('go2.robot_ip', config['go2']['robot_ip']),
        ('lidar.ip', config['lidar']['ip']),
        ('lidar.host_ip', config['lidar']['host_ip']),
    ):
        try:
            ipaddress.IPv4Address(value)
        except ipaddress.AddressValueError as exc:
            raise ValueError(f'{field} must be an IPv4 address.') from exc
    if config['tf'].get('publish_mounts', False):
        validate_mounts(config['tf'])
    return config


def validate_mounts(tf_config):
    if tf_config.get('calibrated') is not True:
        raise ValueError(
            'Mount TF requires tf.calibrated: true and measured xyz/rpy values. '
            'Unmeasured default mounts are not published.'
        )
    children = set()
    for name in ('mid360', 'd435i'):
        mount = tf_config[name]
        parent, child = mount['parent'], mount['child']
        if not parent or not child or parent == child or child in children:
            raise ValueError(f'Invalid/duplicate mount frame for {name}.')
        children.add(child)
        for field in ('xyz', 'rpy'):
            values = mount.get(field)
            if not isinstance(values, list) or len(values) != 3:
                raise ValueError(f'tf.{name}.{field} requires three measured values.')
            if any(isinstance(v, bool) or not isinstance(v, (float, int))
                   or not math.isfinite(v) for v in values):
                raise ValueError(f'tf.{name}.{field} requires finite numbers.')


def lidar_config(config):
    """Keep Livox point coordinates in the physical sensor frame.

    Mount calibration belongs in TF. Applying the same mount here and in TF
    would transform a cloud twice. Livox extrinsic values therefore stay zero.
    """
    lidar = config['lidar']
    host = lidar['host_ip']
    model = lidar.get('model', 'MID360')
    if model not in ('MID360', 'Mid360s'):
        raise ValueError('lidar.model must be MID360 or Mid360s.')
    return {
        'lidar_summary_info': {'lidar_type': 8},
        model: {
            'lidar_net_info': {
                'cmd_data_port': 56100, 'push_msg_port': 56200,
                'point_data_port': 56300, 'imu_data_port': 56400,
                'log_data_port': 56500,
            },
            # Explicit IP mapping initializes sockets before discovery; this also
            # works when Go2 and MID360 use separate LAN interfaces.
            'host_net_info': [{
                'lidar_ip': [lidar['ip']], 'host_ip': host,
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
