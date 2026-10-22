"""Check reference-frame composition against the real pinned Go2 description."""

from pathlib import Path
import math
import xml.etree.ElementTree as ET

import pytest

from wego.configuration import active_mounts, load_config
from wego.robot_description import mounted_description


ROOT = Path(__file__).resolve().parents[1]
GO2 = ROOT.parent / 'go2/driver/go2_description/urdf/go2_description.urdf'


def test_reference_translation_is_relative_to_body_imu_and_has_one_tf_owner():
    config = load_config(ROOT / 'config/robot.yaml')
    original = ET.fromstring(GO2.read_text())
    result = ET.fromstring(mounted_description(GO2.read_text(), active_mounts(config)))
    imu = result.find("joint[@name='imu_joint']")
    mount = result.find("joint[@name='wego_mid360_mount']")
    assert imu.find('parent').get('link') == 'base_link'
    assert imu.find('origin').get('rpy') == '0 0 0'
    assert mount.find('parent').get('link') == 'imu'
    base_xyz = [float(v) for v in imu.find('origin').get('xyz').split()]
    mount_xyz = [float(v) for v in mount.find('origin').get('xyz').split()]
    assert [a + b for a, b in zip(base_xyz, mount_xyz)] == pytest.approx(
        [0.16143, 0.0, 0.12262])
    parents = [j for j in result.findall('joint')
               if j.find('child').get('link') == 'livox_frame']
    assert len(parents) == 1
    assert len(result.findall('link')) == len(original.findall('link')) + 2
    assert result.find("link[@name='livox_frame']/visual") is not None
    assert result.find("link[@name='camera_link']/visual") is not None
    camera_mount = result.find("joint[@name='wego_d435i_mount']")
    assert camera_mount.find('parent').get('link') == 'front_camera'
    camera_xyz = [float(v) for v in camera_mount.find('origin').get('xyz').split()]
    assert camera_xyz == pytest.approx([0.01, 0.0175, 0.05])
    camera_rpy = [float(v) for v in camera_mount.find('origin').get('rpy').split()]
    assert camera_rpy == pytest.approx([0.0, math.radians(5), 0.0])
    # The official visual's lateral offset must cancel at the body midline.
    visual = result.find("link[@name='camera_link']/visual/origin")
    visual_xyz = [float(v) for v in visual.get('xyz').split()]
    assert camera_xyz[1] + visual_xyz[1] == pytest.approx(0.0)
    # ROS x points forward and z up: positive pitch points the lens downward.
    assert -math.sin(camera_rpy[1]) < 0
    front = result.find("joint[@name='front_camera_joint']")
    front_xyz = [float(v) for v in front.find('origin').get('xyz').split()]
    assert [a + b for a, b in zip(front_xyz, camera_xyz)] == pytest.approx(
        [0.33715, 0.01747, 0.09297])
    assert len([j for j in result.findall('joint')
                if j.find('child').get('link') == 'camera_link']) == 1
    # The upstream model is retained, including its original fixed joints.
    for joint in original.findall('joint'):
        assert ET.tostring(result.find(f"joint[@name='{joint.get('name')}']")) == ET.tostring(joint)


def test_misspelled_mount_parent_is_rejected_instead_of_creating_disconnected_model():
    config = load_config(ROOT / 'config/robot.yaml')
    config['tf']['mid360']['parent'] = 'body_imu_typo'
    with pytest.raises(ValueError, match='absent'):
        mounted_description(GO2.read_text(), active_mounts(config))


def test_existing_robot_frame_cannot_acquire_a_second_parent():
    config = load_config(ROOT / 'config/robot.yaml')
    mounts = active_mounts(config)
    mounts['mid360']['child'] = 'radar'
    with pytest.raises(ValueError, match='collides'):
        mounted_description(GO2.read_text(), mounts)
