from glob import glob
from setuptools import find_packages, setup

setup(
    name='wego',
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/wego']),
        ('share/wego', ['package.xml', 'README.md']),
        ('share/wego/launch', glob('launch/*.launch.py')),
        ('share/wego/config', glob('config/*')),
        ('share/wego/rviz', glob('rviz/*.rviz')),
    ],
    install_requires=['setuptools', 'PyYAML'],
    zip_safe=True,
    maintainer='Wego Robotics',
    maintainer_email='go.support@wego-robotics.com',
    description='Go2, MID360 and D435i integrated bringup.',
    license='Apache-2.0',
    entry_points={'console_scripts': [
        'check_hardware = wego.check_hardware:main',
    ]},
)
