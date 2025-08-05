# /qompassai/dotfiles/.config/fish/config.fish
# Qompass AI Fish Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################

if status is-interactive
    set fish_greeting ""
end

for file in ~/.config/fish/conf.d/*.fish
    source $file
end

if command -q zoxide
    zoxide init fish | source
end
set -Ux fish_user_paths $HOME/.local/bin $fish_user_paths
set fish_function_path $fish_function_path ~/.local/share/omf/pkg/foreign-env/functions
abbr -a rm 'rm -Iv'
abbr -a cp 'cp -iv'
abbr -a mv 'mv -iv'
abbr -a gpu 'watch -n 1 nvidia-smi'

