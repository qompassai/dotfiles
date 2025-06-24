#!/usr/bin/env sh
# /qompassai/dotfiles/.profile.d/13-pkgconf.sh
# -----------------------------
# Copyright (C) 2025 Qompass AI, All rights reserved

PKG_PATHS=""
for path in \
    "/opt/QAI/liboqs/lib/pkgconfig" \
    "/opt/cuda/lib64/pkgconfig" \
    "/opt/nvidia/hpc_sdk/Linux_x86_64/25.3/compilers/lib/pkgconfig" \
    "/opt/nvidia/hpc_sdk/Linux_x86_64/25.3/cuda/lib64/pkgconfig" \
    "/opt/nvidia/hpc_sdk/Linux_x86_64/25.3/math_libs/lib64/pkgconfig" \
    "/usr/lib/pkgconfig" \
    "/usr/local/lib/pkgconfig" \
    "/usr/local/share/pkgconfig" \
    "/usr/share/pkgconfig"
do
    if [ -d "$path" ]; then
        PKG_PATHS="${PKG_PATHS:+$PKG_PATHS:}$path"
    fi
done

export PKG_CONFIG_PATH="${PKG_CONFIG_PATH:+$PKG_CONFIG_PATH:}$PKG_PATHS"

export CMAKE_PRESET_FILE="$HOME/CMakePresets.json"
export CMAKE_POLICY_VERSION_MINIMUM="3.5"
if [ -n "$PKG_CONFIG_PATH" ]; then
    PKG_CONFIG_PATH=$(echo "$PKG_CONFIG_PATH" | tr ':' '\n' | awk '!x[$0]++' | grep -v '^$' | paste -sd: -)
    export PKG_CONFIG_PATH
fi
