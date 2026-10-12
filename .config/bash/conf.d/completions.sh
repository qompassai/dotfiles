#!/usr/bin/env bash
# /qompassai/dotfiles/.config/bash/conf.d/completions.sh
# Qompass AI Bash Completions Config
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
# This file was entirely commented out, so nothing below ever ran.
# The user completion tree is the data-side one (it holds a
# completions/ directory, which is what BASH_COMPLETION_USER_DIR
# must point at); the vendored copy that used to sit in
# ~/.config/bash/bash-completion was a dormant duplicate and has
# been removed, its unique specs merged into the user tree.
export BASH_COMPLETION_USER_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/bash/bash-completion"
shopt -s progcomp
if [[ -r /usr/share/bash-completion/bash_completion && -z ${BASH_COMPLETION_VERSINFO:-} ]]; then
    # shellcheck disable=SC1091
    . /usr/share/bash-completion/bash_completion
fi
