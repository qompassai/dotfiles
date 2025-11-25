# /qompassai/dotfiles/.config/fish/conf.d/latex.fish
# Qompass AI Fish LaTeX Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
set -x TEXDIR "$XDG_DATA_HOME/texlive/2025"
set -x TEXMFCONFIG "$XDG_CONFIG_HOME/texlive/texmf-config"
set -x TEXMFHOME "$XDG_DATA_HOME/texmf"
set -x TEXMFVAR "$XDG_CACHE_HOME/texlive/texmf-var"
set -x TEXMFLOCAL "$XDG_DATA_HOME/texlive/texmf-local"
set -x TEXMFSYSCONFIG "$XDG_DATA_HOME/texlive/texmf-sys-config"
set -x TEXMFSYSVAR "$XDG_DATA_HOME/texlive/texmf-sys-var"
set -x INFOPATH "$TEXDIR/texmf-dist/doc/info" $INFOPATH
set -x PATH "$TEXDIR/bin/x86_64-linux" $PATH
set -x MANPATH "$TEXDIR/texmf-dist/doc/man" $MANPATH
