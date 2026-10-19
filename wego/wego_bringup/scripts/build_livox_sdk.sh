#!/usr/bin/env bash
set -eo pipefail
wego_ws_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$wego_ws_root"
cmake -S src/vendor/Livox-SDK2 -B build/livox_sdk2 \
    -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$wego_ws_root/install/wego_vendor"
cmake --build build/livox_sdk2 --parallel "${WEGO_BUILD_JOBS:-2}"
cmake --install build/livox_sdk2
