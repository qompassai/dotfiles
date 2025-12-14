# /qompassai/dotfiles/.config/fish/conf.d/vcpkg.fish
# Qompass AI Fish VCPKG Config
# Copyright (C) 2025 Qompass AI, All rights reserved
# ----------------------------------------
if not set -q VCPKG_DISABLE_METRICS
    set -gx VCPKG_DISABLE_METRICS 1
end
if not set -q VCPKG_ROOT
    set -gx VCPKG_ROOT "$HOME/.local/share/vcpkg"
end
