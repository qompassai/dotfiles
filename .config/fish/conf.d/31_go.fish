# /qompassai/dotfiles/.config/fish/conf.d/go.fish
# Qompass AI Fish Go Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
set -gx GOROOT /usr/lib/go
set -gx GOPATH $HOME/.go
fish_add_path --prepend $GOROOT/bin
fish_add_path --prepend $GOPATH/bin
