"""Attach configured sensor bodies to the upstream Go2 URDF without editing it."""

import xml.etree.ElementTree as ET


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
            if name == 'mid360':
                # Approximate envelope, not collision geometry. Livox's drawing
                # places the point-cloud origin 47 mm above the bottom face.
                visual = ET.SubElement(link, 'visual', name='mid360_envelope')
                ET.SubElement(visual, 'origin', xyz='0 0 -0.017', rpy='0 0 0')
                geometry = ET.SubElement(visual, 'geometry')
                ET.SubElement(geometry, 'box', size='0.065 0.065 0.060')
                material = ET.SubElement(visual, 'material', name='wego_mid360_body')
                ET.SubElement(material, 'color', rgba='0.2 0.35 0.65 1')
            elif name == 'd435i':
                # Official D435(i) visual relative to camera_link; internal
                # optical/IMU transforms remain owned by the RealSense driver.
                visual = ET.SubElement(link, 'visual', name='d435i_body')
                ET.SubElement(visual, 'origin', xyz='0.0043 -0.0175 0',
                              rpy='1.5707963267948966 0 1.5707963267948966')
                geometry = ET.SubElement(visual, 'geometry')
                ET.SubElement(geometry, 'mesh',
                              filename='package://realsense2_description/meshes/d435.dae')
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
