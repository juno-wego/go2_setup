#!/usr/bin/env bash
set -euo pipefail

mid360_package_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
mid360_workspace="${1:-${WEGO_WS_ROOT:-}}"
if [[ -z "$mid360_workspace" ]]; then
    echo 'Usage: build_sdk.sh <workspace> (or set WEGO_WS_ROOT)' >&2
    exit 2
fi
mid360_workspace="$(cd -- "$mid360_workspace" && pwd)"
mid360_build="$mid360_workspace/build/mid360-sdk"

cmake -S "$mid360_package_root/vendor/Livox-SDK2" -B "$mid360_build" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="$mid360_workspace/install/mid360"
cmake --build "$mid360_build" --parallel "${WEGO_BUILD_JOBS:-2}"
cmake --install "$mid360_build"
