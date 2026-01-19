# /qompassai/dotfiles/.config/fish/conf.d/ocaml.fish
# Qompass AI Fish Ocaml Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
set -U fish_user_paths $OPAM_SWITCH_PREFIX/bin $fish_user_paths
if test -r "$HOME/.opam/opam-init/init.fish"
    source "$HOME/.opam/opam-init/init.fish"
end
