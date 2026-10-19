#!/usr/bin/env bash
set -eo pipefail

wego_repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
wego_ws_root="${WEGO_WS_ROOT:-$wego_repo_root}"
mkdir -p "$wego_ws_root"
wego_ws_root="$(cd -- "$wego_ws_root" && pwd)"
wego_ros_distro="${WEGO_ROS_DISTRO:-${ROS_DISTRO:-humble}}"
wego_ros_setup="/opt/ros/$wego_ros_distro/setup.bash"
if [ ! -f "$wego_ros_setup" ]; then
    printf 'ROS setup not found: %s\nSet WEGO_ROS_DISTRO to the installed ROS distribution.\n' \
        "$wego_ros_setup" >&2
    exit 1
fi
source "$wego_ros_setup"

cd "$wego_ws_root"

for required in \
    go2/driver/go2_base/package.xml \
    go2/driver/unitree_ros2/cyclonedds_ws/src/unitree/unitree_go/package.xml \
    go2/driver/unitree_sdk2/CMakeLists.txt \
    mid360/driver/package_ROS2.xml \
    mid360/bringup/vendor/Livox-SDK2/CMakeLists.txt \
    d435i/vendor/librealsense/CMakeLists.txt; do
    if [ ! -f "$wego_repo_root/$required" ]; then
        printf 'Missing source: %s\nRun: git -C "%s" submodule update --init --recursive\n' \
            "$required" "$wego_repo_root" >&2
        exit 1
    fi
done

# Restore DDS types supplied by the SDK but omitted from the ROS message package.
for patch in "$wego_repo_root"/go2/bringup/patches/unitree_ros2-*.patch; do
    [ -f "$patch" ] || continue
    unitree_source="$wego_repo_root/go2/driver/unitree_ros2"
    if git -C "$unitree_source" apply --check "$patch" 2>/dev/null; then
        git -C "$unitree_source" apply "$patch"
    elif ! git -C "$unitree_source" apply --reverse --check "$patch" 2>/dev/null; then
        printf 'Cannot apply Unitree message patch: %s\n' "$patch" >&2
        exit 1
    fi
done

# The upstream driver stores ROS 1/2 manifests separately in a fresh checkout.
cp "$wego_repo_root/mid360/driver/package_ROS2.xml" \
    "$wego_repo_root/mid360/driver/package.xml"

# Keep SDK sources and unused upstream examples out of ROS package discovery.
touch "$wego_repo_root/mid360/bringup/vendor/COLCON_IGNORE"
touch "$wego_repo_root/d435i/vendor/COLCON_IGNORE"
touch "$wego_repo_root/go2/driver/unitree_sdk2/COLCON_IGNORE"
touch "$wego_repo_root/go2/driver/unitree_ros2/example/COLCON_IGNORE"

wego_build_jobs="${WEGO_BUILD_JOBS:-2}"
export MAKEFLAGS="-j$wego_build_jobs"
export CMAKE_BUILD_PARALLEL_LEVEL="$wego_build_jobs"
# Reuse installed SDKs for normal ROS package builds.
if [ ! -f "$wego_ws_root/install/mid360/lib/liblivox_lidar_sdk_shared.so" ]; then
    bash "$wego_repo_root/mid360/bringup/scripts/build_sdk.sh" "$wego_ws_root"
fi
if [ ! -f "$wego_ws_root/install/d435i/lib/librealsense2.so.2.58" ]; then
    bash "$wego_repo_root/d435i/scripts/build_sdk.sh" "$wego_ws_root"
fi
export CMAKE_PREFIX_PATH="$wego_ws_root/install/mid360:$wego_ws_root/install/d435i${CMAKE_PREFIX_PATH:+:$CMAKE_PREFIX_PATH}"
export LD_LIBRARY_PATH="$wego_ws_root/install/mid360/lib:$wego_ws_root/install/d435i/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
colcon build --symlink-install --parallel-workers "$wego_build_jobs" \
    --base-paths "$wego_repo_root/go2" "$wego_repo_root/mid360" \
    "$wego_repo_root/d435i" "$wego_repo_root/wego" \
    --packages-up-to wego \
    --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF \
    -DPython3_EXECUTABLE=/usr/bin/python3 \
    -DROS_EDITION=ROS2 "-DDISTRO_ROS=$wego_ros_distro"
