#!/usr/bin/env sh
# /qompassai/dotfiles/.config/superpaper/scripts/wallpaper_chang.sh
# Qompass AI SuperPaper WallPaper Change Script
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################################
LOGFILE="$HOME/.config/superpaper/wallpaper_change.log"
echo "$(date '+%Y-%m-%d %H:%M:%S') - Wallpaper changed to: $1" >> "$LOGFILE"
if command -v notify-send > /dev/null; then
    notify-send "Superpaper" "Wallpaper changed to: $(basename "$1")"
fi
exit 0
