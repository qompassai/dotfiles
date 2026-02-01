# /qompassai/dotfiles/.config/fish/conf.d/61_vulkan.fish
# Qompass AI Fish Vulkan Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
set -gx VULKAN_SDK "$XDG_DATA_HOME/vulkan"
fish_add_path $VULKAN_SDK/bin
set -gx LD_LIBRARY_PATH "$VULKAN_SDK/lib" $LD_LIBRARY_PATH
set -gx VK_ADD_LAYER_PATH "$VULKAN_SDK/explicit_layer.d" $VK_ADD_LAYER_PATH
set -e VK_LAYER_PATH
