# /qompassai/dotfiles/.config/fish/conf.d/haskell.fish
# Qompass AI Fish Haskell Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
set -gx PATH $HOME/.ghcup/bin $PATH
set -gx CABAL_DIR $HOME/.cabal
set -gx LC_ALL en_US.UTF-8
set -gx NIX_PATH nixpkgs=channel:nixos-unstable
