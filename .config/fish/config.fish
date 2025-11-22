# /qompassai/dotfiles/.config/fish/config.fish
# Qompass AI Fish Config
# Copyright (C) 2025 Qompass AI, All rights reserved
#---------------------------------------------------
if status is-interactive
    set fish_greeting ""
end
for file in ~/.config/fish/conf.d/*.fish
    source $file
end
if command -q zoxide
    zoxide init fish | source
end
#eval (ssh-agent -c)
set fish_function_path $fish_function_path ~/.local/share/omf/pkg/foreign-env/functions

set -x PATH $HOME/.dotnet $PATH
set -x DOTNET_ROOT $HOME/.dotnet
