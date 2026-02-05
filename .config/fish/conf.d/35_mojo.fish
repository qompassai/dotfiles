# /qompassai/dotfiles/.config/fish/conf.d/35_mojo.fish
# Qompass AI Fish Mojo Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
pixi completion --shell fish | source
set -gx MOJO_HOME "$XDG_DATA_HOME/mojo/.pixi/envs/default"
set -gx CPATH "$MOJO_HOME/include:$CPATH"
set -gx C_INCLUDE_PATH "$MOJO_HOME/include:$C_INCLUDE_PATH"
set -gx CPLUS_INCLUDE_PATH "$MOJO_HOME/include:$CPLUS_INCLUDE_PATH"
set -gx LD_LIBRARY_PATH "$MOJO_HOME/lib:$LD_LIBRARY_PATH"
set -gx MANPATH "$MOJO_HOME/man:$MOJO_HOME/share/man:$MANPATH"
set -gx MOJO_STDLIB_PATH "$MOJO_HOME/lib/mojo"
set -gx PKG_CONFIG_PATH "$MOJO_HOME/lib/pkgconfig:$PKG_CONFIG_PATH"
fish_add_path "$MOJO_HOME/bin"
