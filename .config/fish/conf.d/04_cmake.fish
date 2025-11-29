# /qompassai/dotfiles/.config/fish/conf.d/cmake.fish
# Qompass AI Fish CMake Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
function cmake
    command cmake -DCMAKE_POLICY_VERSION_MINIMUM=3.30 $argv
end
set -x CMAKE_PREFIX_PATH /usr/lib/cmake/Boost-1.89.0
set -x boost_system_DIR /usr/lib/cmake/Boost-1.89.0

