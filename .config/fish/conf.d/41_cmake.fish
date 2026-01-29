# /qompassai/dotfiles/.config/fish/conf.d/cmake.fish
# Qompass AI Fish CMake Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
set -gx CMAKE_EXPORT_COMPILE_COMMANDS ON
set -gx CMAKE_BUILD_PARALLEL_LEVEL 8
set -gx CMAKE_COLOR_DIAGNOSTICS ON
set -gx CMAKE_PREFIX_PATH "$HOME/.local;/opt/llvm"
set -gx CMAKE_GENERATOR Ninja
