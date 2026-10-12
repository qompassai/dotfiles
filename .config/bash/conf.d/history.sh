#!/usr/bin/env bash
# /qompassai/dotfiles/.config/bash/conf.d/history.sh
# Qompass AI Bash History Config
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
# History had no configuration at all: it defaulted to
# ~/.bash_history with histappend off. It now lives under
# XDG_STATE_HOME with explicit sizes and controls.
export HISTCONTROL='ignoreboth:erasedups'
export HISTFILE="${XDG_STATE_HOME:-$HOME/.local/state}/bash/history"
export HISTFILESIZE=100000
export HISTIGNORE='bg:exit:fg:history:la:ll:ls'
export HISTSIZE=50000
export HISTTIMEFORMAT='%F %T '
shopt -s cmdhist
shopt -s histappend
shopt -s lithist
mkdir -p "${HISTFILE%/*}"
