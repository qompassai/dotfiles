# /qompassai/dotfiles/.config/fish/vulkan.fish
# Qompass AI Fish Vulkan Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
set ARCH (uname -m)
set VULKAN_SDK "$HOME/.local/share/vulkan-sdk/$ARCH"
set PATH "$VULKAN_SDK/bin" $PATH
set LD_LIBRARY_PATH "$VULKAN_SDK/lib" $LD_LIBRARY_PATH
set VK_ADD_LAYER_PATH "$VULKAN_SDK/share/vulkan/explicit_layer.d" $VK_ADD_LAYER_PATH
set -e VK_LAYER_PATH
