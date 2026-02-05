#!/usr/bin/env bash
# /qompassai/dotfiles/.config/bash/conf.d/mojo.sh
# Qompass AI Bash Mojo Config
# Copyright (C) 2026 Qompass AI, All rights reserved
# --------------------------------------------------
eval "$(pixi completion --shell bash)"
export MOJO_HOME="$HOME/.local/share/mojo/.pixi/envs/default"
export CPATH="$MOJO_HOME/include:$CPATH"
export C_INCLUDE_PATH="$MOJO_HOME/include:$C_INCLUDE_PATH"
export CPLUS_INCLUDE_PATH="$MOJO_HOME/include:$CPLUS_INCLUDE_PATH"
export LD_LIBRARY_PATH="$MOJO_HOME/lib:$LD_LIBRARY_PATH"
export MANPATH="$MOJO_HOME/man:$MOJO_HOME/share/man:$MANPATH"
export MOJO_STDLIB_PATH="$MOJO_HOME/lib/mojo"
export PKG_CONFIG_PATH="$MOJO_HOME/lib/pkgconfig:$PKG_CONFIG_PATH"
export PATH="$MOJO_HOME/bin:$PATH"
