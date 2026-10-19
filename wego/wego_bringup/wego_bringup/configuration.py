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
    """Validate enabled mounts, retaining reference versus measured provenance."""
    children = set()
    mounts = {}
    for name in ('mid360', 'd435i'):
        mount = tf_config[name]
        if mount.get('enabled') is not True:
            continue
        if mount.get('status') not in ('reference', 'measured'):
            raise ValueError(f'tf.{name} needs a reference or measured mount status.')
        if mount['status'] == 'reference' and not mount.get('source'):
            raise ValueError(f'tf.{name} reference mount requires a source.')
        parent, child = mount['parent'], mount['child']
        if not parent or not child or parent == child or child in children:
            raise ValueError(f'Invalid/duplicate mount frame for {name}.')
        children.add(child)
        for field in ('xyz', 'rpy'):
            values = mount.get(field)
            if not isinstance(values, list) or len(values) != 3:
                raise ValueError(f'tf.{name}.{field} requires three pose values.')
            if any(isinstance(v, bool) or not isinstance(v, (float, int))
                   or not math.isfinite(v) for v in values):
                raise ValueError(f'tf.{name}.{field} requires finite numbers.')
        mounts[name] = mount
    # A mount may be attached to another mount, but must not create a TF cycle.
    parents = {mount['child']: mount['parent'] for mount in mounts.values()}
    for child in parents:
        visited = set()
        frame = child
        while frame in parents:
            if frame in visited:
                raise ValueError('Sensor mount TF contains a cycle.')
            visited.add(frame)
            frame = parents[frame]
    return mounts


def active_mounts(config):
    """Return only configured mounts whose sensor is part of this launch."""
    if config['tf'].get('publish_mounts') is not True:
        return {}
    mounts = validate_mounts(config['tf'])
    sections = {'mid360': 'lidar', 'd435i': 'camera'}
    expected = {'mid360': config['lidar']['frame_id'],
                'd435i': config['camera']['name'] + '_link'}
    result = {}
    for name, mount in mounts.items():
        if not config[sections[name]]['enabled']:
            continue
        if mount['child'] != expected[name]:
            raise ValueError(f'tf.{name}.child must match driver frame {expected[name]}.')
        result[name] = mount
    return result


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
