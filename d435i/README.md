# D435i

Standalone RealSense D435i support. This package owns its configuration,
librealsense sources in `d435i/vendor/librealsense`, SDK build script and launch file.
The ROS driver and camera description remain upstream packages.

Build the SDK before building the ROS workspace:

```bash
./d435i/scripts/build_sdk.sh /path/to/workspace
```

The script retains the RSUSB backend and disables CUDA, examples and tools.
It installs into `<workspace>/install/d435i`. The workspace build tools expose
that prefix while compiling the driver; sourcing the resulting workspace
exposes its SDK libraries through the package environment hook.

After building and sourcing the workspace:

```bash
ros2 launch d435i bringup.launch.py
ros2 launch d435i bringup.launch.py config_file:=/path/to/device.yaml
```

Device YAML is a flat mapping using the fields in `config/device.yaml`.
An empty `serial_no` selects the attached camera; robot profiles may pin one.
RealSense publishes its internal TF. Robot-specific mounting transforms belong
to `wego`. This package does not configure Go2 or DDS interfaces.
