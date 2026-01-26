#!/usr/bin/env bash
# /qompassai/dotfiles/.config/bash/conf.d/completions.sh
# Qompass AI Bash Completions Config
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
shopt -s progcomp
export BASH_COMPLETION_USER_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/bash/bash-completion/bash_completion"
if [[ $PS1 ]]; then
  [[ -r /usr/share/bash-completion/bash_completion ]] && . /usr/share/bash-completion/bash_completion
fi
