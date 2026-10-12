#!/usr/bin/env bash
# $XDG_CONFIG_HOME/bash/conf.d/00_xdg.sh
# Qompass AI Bash XDG Config
# Copyright (C) 2026 Qompass AI, All rights reserved
####################################################
# Reference: https://wiki.archlinux.org/title/XDG_Base_Directory
# Every XDG variable is set explicitly. User directories match
# ~/.config/user-dirs.dirs exactly (that file is the standard
# mechanism; these exports mirror it for programs that read the
# environment instead).
export LANG=en_US.UTF-8
case ":$PATH:" in
    *":$HOME/.local/bin:"*) ;;
    *) export PATH="$HOME/.local/bin:$PATH" ;;
esac
export XDG_BIN_HOME="$HOME/.local/bin"
export XDG_CACHE_HOME="$HOME/.cache"
export XDG_CONFIG_DIRS="/etc/xdg:/usr/local/etc/xdg"
export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
export XDG_CURRENT_DESKTOP=Hyprland
export XDG_DATA_DIRS="$HOME/.local/share:/usr/local/share:/usr/share"
export XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
export XDG_DESKTOP_DIR="$HOME/.Desktop"
export XDG_DESKTOP_PORTAL_DIR="${XDG_RUNTIME_DIR:-/run/user/$UID}/xdg-desktop-portal/portals"
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
# Readline configuration lives in the XDG tree, not ~/.inputrc.
export INPUTRC="${XDG_CONFIG_HOME:-$HOME/.config}/readline/inputrc"
