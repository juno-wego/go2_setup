# Go2

Go2 driver composition, bridge parameters and native sensor adapters belong here.
The upstream `go2_base`, `go2_description` and Unitree messages remain in
`go2/driver`, alongside this package at `go2/bringup`.
This package does not depend on `wego` or external sensors.

```bash
ros2 launch go2 bringup.launch.py
ros2 launch go2 bringup.launch.py config_file:=/path/to/go2.yaml rviz:=true
```

`config/device.yaml` contains the standalone network interface, robot IP used by
diagnostics, and DDS domain. `config/go2.yaml` contains the upstream ROS node
parameters. The launch selects CycloneDDS and validates the configured interface
only within its Go2 scope. An empty interface leaves DDS interface selection to
the environment.
Control, state bridging, robot description and the `go2_sensors` node start together;
the bridge parameters keep automatic standing and mode changes disabled.

The optional `description_file` launch argument accepts an assembled URDF. It
defaults to the upstream Go2 URDF; sensor mounting TF belongs to `wego`.
