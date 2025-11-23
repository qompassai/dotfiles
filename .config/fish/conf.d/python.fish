# /qompassai/dotfiles/.config/fish/conf.d/python.fish
# Qompass AI Fish Python Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
if command -q pyenv
    pyenv init - | source
end
