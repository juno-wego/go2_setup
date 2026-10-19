"""Attach configured sensor bodies to the upstream Go2 URDF without editing it."""

import xml.etree.ElementTree as ET

from mid360.description import add_visual as add_mid360_visual
from d435i.description import add_visual as add_d435i_visual

SENSOR_VISUALS = {'mid360': add_mid360_visual, 'd435i': add_d435i_visual}


def mounted_description(description, mounts):
    robot = ET.fromstring(description)
    links = {link.attrib['name'] for link in robot.findall('link')}
    joints = {joint.attrib['name'] for joint in robot.findall('joint')}
    pending = dict(mounts)
    while pending:
        added = False
        for name, mount in list(pending.items()):
            if mount['parent'] not in links:
                continue
            child = mount['child']
            joint_name = 'wego_' + name + '_mount'
            if child in links or joint_name in joints:
                raise ValueError(f'Mount {name} collides with an existing URDF frame/joint.')
            link = ET.SubElement(robot, 'link', name=child)
            if name in SENSOR_VISUALS:
                SENSOR_VISUALS[name](link)
            joint = ET.SubElement(robot, 'joint', name=joint_name, type='fixed')
            ET.SubElement(joint, 'parent', link=mount['parent'])
            ET.SubElement(joint, 'child', link=child)
            ET.SubElement(joint, 'origin',
                          xyz=' '.join(str(v) for v in mount['xyz']),
                          rpy=' '.join(str(v) for v in mount['rpy']))
            links.add(child)
            joints.add(joint_name)
            del pending[name]
            added = True
        if not added:
            raise ValueError('Mount parent frames are absent from the Go2 URDF: '
                             + ', '.join(mount['parent'] for mount in pending.values()))
    return ET.tostring(robot, encoding='unicode')
