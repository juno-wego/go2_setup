#!/usr/bin/env bash
set -eo pipefail

wego_ws_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../../.." && pwd)"
wego_src_root="$wego_ws_root/src"

for required in \
    drivers/go2/go2_base/package.xml \
    drivers/go2/unitree_ros2/cyclonedds_ws/src/unitree/unitree_go/package.xml \
    drivers/go2/unitree_sdk2/CMakeLists.txt \
    drivers/livox_ros_driver2/package_ROS2.xml \
    vendor/Livox-SDK2/CMakeLists.txt \
    vendor/librealsense/CMakeLists.txt; do
    if [ ! -f "$wego_src_root/$required" ]; then
        printf 'Missing source: %s\nRun: git -C "%s" submodule update --init --recursive\n' \
            "$required" "$wego_src_root" >&2
        exit 1
    fi
done

# Restore DDS types supplied by the SDK but omitted from the ROS message package.
for patch in "$wego_src_root"/wego/wego_bringup/patches/unitree_ros2-*.patch; do
    [ -f "$patch" ] || continue
    unitree_source="$wego_src_root/drivers/go2/unitree_ros2"
    if git -C "$unitree_source" apply --check "$patch" 2>/dev/null; then
        git -C "$unitree_source" apply "$patch"
    elif ! git -C "$unitree_source" apply --reverse --check "$patch" 2>/dev/null; then
        printf 'Cannot apply Unitree message patch: %s\n' "$patch" >&2
        exit 1
    fi
done

# The upstream driver stores ROS 1/2 manifests separately in a fresh checkout.
cp "$wego_src_root/drivers/livox_ros_driver2/package_ROS2.xml" \
    "$wego_src_root/drivers/livox_ros_driver2/package.xml"

# Keep SDK sources and unused upstream examples out of ROS package discovery.
touch "$wego_src_root/vendor/COLCON_IGNORE"
touch "$wego_src_root/drivers/go2/unitree_sdk2/COLCON_IGNORE"
touch "$wego_src_root/drivers/go2/unitree_ros2/example/COLCON_IGNORE"
