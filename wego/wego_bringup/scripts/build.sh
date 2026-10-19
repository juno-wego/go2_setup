#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/humble/setup.bash
wego_ws_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$wego_ws_root"
bash src/wego/wego_bringup/scripts/prepare_sources.sh
export MAKEFLAGS=-j2
export CMAKE_BUILD_PARALLEL_LEVEL=2
# Reuse installed SDKs for normal ROS package builds.
if [ ! -f install/wego_vendor/lib/liblivox_lidar_sdk_shared.so ]; then
    bash src/wego/wego_bringup/scripts/build_livox_sdk.sh
fi
if [ ! -f install/wego_vendor/lib/librealsense2.so.2.58 ]; then
    bash src/wego/wego_bringup/scripts/build_realsense_sdk.sh
fi
export CMAKE_PREFIX_PATH="$wego_ws_root/install/wego_vendor${CMAKE_PREFIX_PATH:+:$CMAKE_PREFIX_PATH}"
export LD_LIBRARY_PATH="$wego_ws_root/install/wego_vendor/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
colcon build --symlink-install --parallel-workers 2 \
    --packages-select unitree_go unitree_api go2_interface go2_description \
    go2_base livox_ros_driver2 wego_vendor wego_bringup \
    --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF \
    -DROS_EDITION=ROS2 -DDISTRO_ROS=humble
