#!/usr/bin/env bash
set -eo pipefail
wego_ws_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$wego_ws_root"
cmake -S src/vendor/librealsense -B build/librealsense-rsusb \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="$wego_ws_root/install/wego_vendor" \
    -DFORCE_RSUSB_BACKEND=ON -DBUILD_WITH_CUDA=OFF \
    -DBUILD_EXAMPLES=OFF -DBUILD_GRAPHICAL_EXAMPLES=OFF \
    -DBUILD_GLSL_EXTENSIONS=OFF -DBUILD_TOOLS=OFF \
    -DBUILD_ROSBAG2=OFF -DBUILD_RS2_ALL=OFF \
    -DBUILD_WITH_DDS=OFF -DCHECK_FOR_UPDATES=OFF
cmake --build build/librealsense-rsusb --parallel "${WEGO_BUILD_JOBS:-2}"
cmake --install build/librealsense-rsusb
