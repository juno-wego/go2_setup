"""RViz views for measured mount TF and independent sensor inspection."""

from pathlib import Path
import copy
import shutil
import tempfile

import yaml

from wego.configuration import active_mounts


def _enable(display, enabled):
    display['Enabled'] = bool(enabled)
    display['Value'] = bool(enabled)


def write_rviz_configs(config, template_dir, output_dir):
    """Render views without adding or guessing any sensor mounting transform."""
    template_dir, output_dir = Path(template_dir), Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    robot = yaml.safe_load((template_dir / 'robot_sensors.rviz').read_text())
    lidar = config['lidar']
    camera = config['camera']
    camera_enabled = camera['enabled']
    lidar_enabled = lidar['enabled']
    robot_enabled = config['go2']['enabled']
    mounts = active_mounts(config)
    fixed_frame = 'odom'
    if not robot_enabled:
        if camera_enabled:
            fixed_frame = camera['name'] + '_link'
        elif lidar_enabled:
            fixed_frame = lidar['frame_id']
    robot['Visualization Manager']['Global Options']['Fixed Frame'] = fixed_frame
    camera_prefix = '/' + '/'.join(
        str(v).strip('/') for v in (camera['namespace'], camera['name'])
        if str(v).strip('/'))
    camera_frame = camera['name'] + '_link'
    camera_cloud_available = camera_enabled and camera['pointcloud']
    camera_in_robot = camera_cloud_available and (
        (robot_enabled and 'd435i' in mounts) or fixed_frame == camera_frame)
    cloud_available = lidar_enabled and int(lidar['xfer_format']) == 0
    lidar_in_robot = cloud_available and (
        (robot_enabled and 'mid360' in mounts) or fixed_frame == lidar['frame_id'])
    displays = []
    for display in robot['Visualization Manager']['Displays']:
        name = display['Name']
        if name == 'Go2 Robot':
            _enable(display, robot_enabled)
        elif name in ('Go2 Camera', 'Go2 LiDAR'):
            if not robot_enabled:
                continue
            _enable(display, True)
        elif name in ('D435i RGB', 'D435i Depth'):
            if not camera_enabled:
                robot.get('Window Geometry', {}).pop(name, None)
                continue
            suffix = ('color/image_raw' if name == 'D435i RGB'
                      else 'depth/image_rect_raw')
            display['Topic']['Value'] = camera_prefix + '/' + suffix
            _enable(display, True)
        elif name == 'MID360 Cloud':
            _enable(display, lidar_in_robot)
        elif name == 'D435i Cloud':
            display['Topic']['Value'] = camera_prefix + '/depth/color/points'
            _enable(display, camera_in_robot)
        displays.append(display)
    robot['Visualization Manager']['Displays'] = displays
    paths = {'robot': output_dir / 'robot_sensors.rviz'}
    paths['robot'].write_text(yaml.safe_dump(robot, sort_keys=False))
    if cloud_available and not lidar_in_robot:
        preview = yaml.safe_load((template_dir / 'lidar.rviz').read_text())
        preview['Visualization Manager']['Global Options']['Fixed Frame'] = lidar['frame_id']
        paths['lidar'] = output_dir / 'mid360_sensor_frame.rviz'
        paths['lidar'].write_text(yaml.safe_dump(preview, sort_keys=False))
    if camera_cloud_available and not camera_in_robot:
        preview = copy.deepcopy(robot)
        manager = preview['Visualization Manager']
        manager['Global Options']['Fixed Frame'] = camera_frame
        manager['Displays'] = [display for display in manager['Displays']
                               if display['Name'] in ('Grid', 'TF', 'D435i Cloud')]
        for display in manager['Displays']:
            _enable(display, True)
        manager['Views']['Current'].update({
            'Distance': 3.5, 'Focal Point': {'X': 1.5, 'Y': 0, 'Z': 0}})
        preview['Window Geometry'].update(Width=900, Height=900, X=990, Y=80)
        paths['camera'] = output_dir / 'd435i_sensor_frame.rviz'
        paths['camera'].write_text(yaml.safe_dump(preview, sort_keys=False))
    return paths


def rviz_actions(config, template_dir):
    """Create managed RViz nodes and previews for sensors without mounting TF."""
    from launch.actions import LogInfo, OpaqueFunction, RegisterEventHandler
    from launch.event_handlers import OnShutdown
    from launch_ros.actions import Node

    folder = tempfile.mkdtemp(prefix='wego-rviz-')
    try:
        paths = write_rviz_configs(config, template_dir, folder)
    except Exception:
        shutil.rmtree(folder, ignore_errors=True)
        raise

    def cleanup(context):
        shutil.rmtree(folder, ignore_errors=True)
        return []

    actions = [RegisterEventHandler(OnShutdown(on_shutdown=[
        OpaqueFunction(function=cleanup),
    ]))]
    if 'lidar' in paths:
        # An alias at the same sensor origin lets RViz register this standalone
        # frame in TF. It defines display axes only, with no robot mount relation.
        frame = config['lidar']['frame_id']
        actions.append(Node(
            package='tf2_ros', executable='static_transform_publisher',
            name='wego_lidar_view_axes', output='screen',
            arguments=[
                '--x', '0', '--y', '0', '--z', '0',
                '--roll', '0', '--pitch', '0', '--yaw', '0',
                '--frame-id', frame, '--child-frame-id', frame + '_rviz_axes',
            ],
        ))
        actions.append(LogInfo(msg=(
            'MID360 is shown in a separate sensor-frame RViz window until '
            'measured mounting TF is enabled. RGB/depth images are in the robot window.'
        )))
    if 'camera' in paths:
        actions.append(LogInfo(msg=(
            'D435i pointcloud is shown in a separate camera-frame RViz window '
            'until its measured mounting TF is enabled.'
        )))
    if config['lidar']['enabled'] and int(config['lidar']['xfer_format']) != 0:
        actions.append(LogInfo(msg=(
            'RViz PointCloud2 needs lidar.xfer_format: 0. '
            'Livox CustomMsg is not a PointCloud2 display input.'
        )))
    for key, path in paths.items():
        actions.append(Node(
            package='rviz2', executable='rviz2',
            name={'robot': 'wego_rviz', 'lidar': 'wego_lidar_rviz',
                  'camera': 'wego_camera_rviz'}[key],
            arguments=['-d', str(path)], output='screen',
        ))
    return actions
