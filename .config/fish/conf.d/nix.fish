# /qompassai/dotfiles/fish/conf.d/nix.fish
# Qompass AI Fish Nix Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
set -gx XDG_DATA_DIRS $HOME/.nix-profile/share $HOME/.local/share /usr/local/share /usr/share
set -x NIX_INCLUDE_PATH $HOME/.nix-profile/include

