"""Official MID-360S CAD visual in the driver's point-cloud frame."""

import xml.etree.ElementTree as ET


def add_visual(link):
    """Attach the connected sensor's CAD mesh without changing mounting TF."""
    # The mesh is already in metres and the Livox frame (origin 47 mm above base).
    # Conversion and manufacturer provenance are recorded in meshes/README.md.
    visual = ET.SubElement(link, 'visual', name='mid360_body')
    ET.SubElement(visual, 'origin', xyz='0 0 0', rpy='0 0 0')
    geometry = ET.SubElement(visual, 'geometry')
    ET.SubElement(geometry, 'mesh', filename='package://mid360/meshes/mid360s.stl')
    material = ET.SubElement(visual, 'material', name='wego_mid360_body')
    ET.SubElement(material, 'color', rgba='0.55 0.58 0.62 1')
