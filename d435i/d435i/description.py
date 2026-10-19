"""D435i visual geometry, independent of its mounting pose."""

import xml.etree.ElementTree as ET


def add_visual(link):
    """Add the official D435(i) visual relative to an existing camera_link."""
    # The driver continues to own internal camera optical and IMU transforms.
    visual = ET.SubElement(link, 'visual', name='d435i_body')
    ET.SubElement(visual, 'origin', xyz='0.0043 -0.0175 0',
                  rpy='1.5707963267948966 0 1.5707963267948966')
    geometry = ET.SubElement(visual, 'geometry')
    ET.SubElement(geometry, 'mesh',
                  filename='package://realsense2_description/meshes/d435.dae')
