#!/usr/bin/env bash
# /qompassai/dotfiles/.config/bash/conf.d/utils.sh
# Qompass AI Bash Utils Config
# Copyright (C) 2026 Qompass AI, All rights reserved
####################################################
if command -v lsd > /dev/null 2>&1; then
    alias ls='command lsd'
    alias ll='ls -l --icon always'
    alias la='ls -a --icon always'
    alias tree='ls --tree'
elif command -v eza > /dev/null 2>&1; then
    alias ls='command eza'
    alias ll='ls -l --icons=auto'
    alias la='ls -a --icons=auto'
fi
bind 'set show-all-if-ambiguous on'
bind 'set completion-ignore-case on'
bind 'set completion-map-case on'
bind '"\e[Z": menu-complete-backward'
