#!/usr/bin/env bash
set -euo pipefail

d435i_package_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
d435i_workspace="${1:-${WEGO_WS_ROOT:-}}"
if [[ -z "$d435i_workspace" ]]; then
    echo 'Usage: build_sdk.sh <workspace> (or set WEGO_WS_ROOT)' >&2
    exit 2
fi
d435i_workspace="$(cd -- "$d435i_workspace" && pwd)"
d435i_build="$d435i_workspace/build/d435i-sdk"

cmake -S "$d435i_package_root/vendor/librealsense" -B "$d435i_build" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="$d435i_workspace/install/d435i" \
    -DFORCE_RSUSB_BACKEND=ON -DBUILD_WITH_CUDA=OFF \
    -DBUILD_EXAMPLES=OFF -DBUILD_GRAPHICAL_EXAMPLES=OFF \
    -DBUILD_GLSL_EXTENSIONS=OFF -DBUILD_TOOLS=OFF \
    -DBUILD_ROSBAG2=OFF -DBUILD_RS2_ALL=OFF \
    -DBUILD_WITH_DDS=OFF -DCHECK_FOR_UPDATES=OFF
cmake --build "$d435i_build" --parallel "${WEGO_BUILD_JOBS:-2}"
cmake --install "$d435i_build"
