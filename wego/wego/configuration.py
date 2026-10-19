"""Configuration shared by the launch file and hardware diagnostic."""

import math
from pathlib import Path

import yaml

from go2.configuration import DEFAULT_CONFIG as GO2_DEFAULTS, normalize_config as normalize_go2
from mid360.configuration import DEFAULT_CONFIG as MID360_DEFAULTS, normalize_config as normalize_mid360
from d435i.configuration import DEFAULT_CONFIG as D435I_DEFAULTS, normalize_config as normalize_d435i


def _device(config, section, defaults, normalize):
    values = config.get(section, {})
    if not isinstance(values, dict):
        raise ValueError(f'{section} must be a YAML mapping.')
    values = dict(values)
    enabled = values.pop('enabled', False)
    if not isinstance(enabled, bool):
        raise ValueError(f'{section}.enabled must be true or false.')
    # Disabled devices do not require valid addresses or an installed interface.
    settings = normalize(values) if enabled else {**defaults, **values}
    return {**settings, 'enabled': enabled}


def load_config(path):
    config = yaml.safe_load(Path(path).read_text())
    if not isinstance(config, dict):
        raise ValueError('Robot configuration must be a YAML mapping.')
    result = {
        'go2': _device(config, 'go2', GO2_DEFAULTS, normalize_go2),
        'lidar': _device(config, 'lidar', MID360_DEFAULTS, normalize_mid360),
        'camera': _device(config, 'camera', D435I_DEFAULTS, normalize_d435i),
    }
    tf = config.get('tf', {})
    if not isinstance(tf, dict):
        raise ValueError('tf must be a YAML mapping.')
    tf = dict(tf)
    publish = tf.get('publish_mounts', False)
    if not isinstance(publish, bool):
        raise ValueError('tf.publish_mounts must be true or false.')
    tf['publish_mounts'] = publish
    for name in ('mid360', 'd435i'):
        mount = tf.get(name, {})
        if not isinstance(mount, dict):
            raise ValueError(f'tf.{name} must be a YAML mapping.')
        tf[name] = {'enabled': False, **mount}
    result['tf'] = tf
    if publish:
        validate_mounts(tf)
    return result


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
