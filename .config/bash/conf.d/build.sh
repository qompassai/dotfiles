#!/usr/bin/env bash
# /qompassai/dotfiles/.config/bash/conf.d/build.sh
# Qompass AI Bash Build Script (buildcache + CMake)
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
# All buildcache configuration is consolidated here; it was formerly
# defined in three places (~/.bashrc, cuda.sh, lua.sh) with drifting
# values. The Django-Ninja exports that used to sit in this file
# moved to django.sh, where they belong.
export BUILDCACHE_CC=/usr/bin/clang
export BUILDCACHE_CONFIG_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/buildcache/config.json"
export BUILDCACHE_CXX=/usr/bin/clang++
export BUILDCACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/buildcache"
export BUILDCACHE_LUA_PATH="${XDG_CONFIG_HOME:-$HOME/.config}/buildcache/lua"
export BUILDCACHE_MAX_CACHE_SIZE=50000000000 # bytes; 50G
export CMAKE_C_COMPILER_LAUNCHER=buildcache
export CMAKE_CXX_COMPILER_LAUNCHER=buildcache
export CMAKE_POLICY_VERSION_MINIMUM=4.4.0
#vim: set filetype=sh:
