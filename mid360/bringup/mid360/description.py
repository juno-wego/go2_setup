"""MID360 visual geometry, independent of its mounting pose."""

import xml.etree.ElementTree as ET


def add_visual(link):
    """Add the approximate sensor envelope to an existing URDF link."""
    # Livox's drawing places the point-cloud origin 47 mm above the bottom face.
    # This is a visual approximation, not collision geometry.
    visual = ET.SubElement(link, 'visual', name='mid360_envelope')
    ET.SubElement(visual, 'origin', xyz='0 0 -0.017', rpy='0 0 0')
    geometry = ET.SubElement(visual, 'geometry')
    ET.SubElement(geometry, 'box', size='0.065 0.065 0.060')
    material = ET.SubElement(visual, 'material', name='wego_mid360_body')
    ET.SubElement(material, 'color', rgba='0.2 0.35 0.65 1')
