# /qompassai/dotfiles/.config/fish/config.fish
# Qompass AI Fish Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
if status is-interactive
    set fish_greeting ""
end
for file in $XDG_CONFIG_HOME/fish/conf.d/*.fish
    source $file
end
if command -v zoxide >/dev/null 2>&1
    zoxide init fish | source
end
set fish_function_path $fish_function_path $XDG_DATA_HOME/omf/pkg/foreign-env/functions
fish_add_path --prepend $HOME/.local/bin
fish_add_path --prepend $HOME/.local/share/lua/bin
fish_add_path /usr/local/bin /usr/local/sbin /usr/bin /usr/sbin
