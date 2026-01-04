# /qompassai/dotfiles/.config/fish/conf.d/pascal.fish
# Qompass AI Fish Pascal Config
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
if not set -q XDG_DATA_HOME
    set -x XDG_DATA_HOME "$HOME/.local/share"
end
set -x FPCDIR "$XDG_DATA_HOME/fpc/src"
set -x PP "$XDG_DATA_HOME/fpc/bin/ppcx64"
set -x LAZARUSDIR "$XDG_DATA_HOME/lazarus"
set -x FPCTARGET 'linux'
set -x FPCTARGETCPU 'x86_64'
if not contains "$XDG_DATA_HOME/fpc/bin" $PATH
    set -x PATH "$XDG_DATA_HOME/fpc/bin" $PATH
end

