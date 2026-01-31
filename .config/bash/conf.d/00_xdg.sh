#!/usr/bin/env bash
# $XDG_CONFIG_HOME/bash/conf.d/00_xdg.sh
# Qompass AI Bash XDG Config
# Copyright (C) 2026 Qompass AI, All rights reserved
####################################################
# Reference: https://wiki.archlinux.org/title/XDG_Base_Directory
export LANG=en_US.UTF-8
export PATH="$HOME/.local/bin:$PATH"
export XDG_BIN_HOME="$HOME/.local/bin:/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin"
export XDG_CACHE_HOME="$HOME/.cache"
export XDG_CONFIG_DIRS="$HOME/.config/xdg:/etc/xdg:/usr/local/etc/xdg:/usr/etc/xdg"
export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
export XDG_CURRENT_DESKTOP=Hyprland
export XDG_CURRENT_SESSION=Hyprland
export XDG_DATA_DIRS="$HOME/.local/share:/usr/local/share:/usr/share"
export XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
export XDG_DESKTOP_DIR="$HOME/.Desktop"
export XDG_DESKTOP_PORTAL_DIR="/run/user/1000/xdg-desktop-portal/portals"
export XDG_DOCUMENTS_DIR="$HOME/.Documents"
export XDG_DOWNLOAD_DIR="$HOME/.Downloads"
export XDG_LIB_HOME="$HOME/.local/lib"
export XDG_MUSIC_DIR="$HOME/.Music"
export XDG_PICTURES_DIR="$HOME/.Pictures"
export XDG_PUBLICSHARE_DIR="$HOME/.Public"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$UID}"
export XDG_SESSION_DESKTOP=Hyprland
export XDG_SESSION_TYPE=wayland
export XDG_STATE_HOME="${XDG_STATE_HOME:-$HOME/.local/state}"
export XDG_TEMPLATES_DIR="$HOME/.Templates"
export XDG_UTILS_DEBUG_LEVEL=3
export XDG_VIDEOS_DIR="$HOME/.Videos"
