from glob import glob
from setuptools import find_packages, setup


setup(
    name='go2',
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/go2']),
        ('share/go2', ['package.xml', 'README.md']),
        ('share/go2/launch', glob('launch/*.launch.py')),
        ('share/go2/config', glob('config/*.yaml')),
    ],
    install_requires=['setuptools', 'PyYAML'],
    zip_safe=True,
    maintainer='Wego Robotics',
    maintainer_email='go.support@wego-robotics.com',
    description='Standalone Go2 bringup and native sensor adapters.',
    license='Apache-2.0',
    entry_points={'console_scripts': ['go2_sensors = go2.go2_sensors:main']},
)
