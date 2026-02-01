# /qompassai/dotfiles/.config/fish/conf.d/xdg.fish
# Qompass AI Fish X Desktop Group (XDG) Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
set -gx INFODIR $HOME/.local/share/info:/usr/local/share/info:/usr/share/info
set -gx LANG en_US.UTF-8
set -gx LC_ALL en_US.UTF-8
set -gx MANPATH $HOME/.local/share/man:/usr/local/share/man:/usr/share/man
fish_add_path --prepend $HOME/.local/bin
set -gx XDG_BIN_HOME $HOME/.local/bin:/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin
set -gx XDG_CACHE_HOME $HOME/.cache
set -gx XDG_CONFIG_DIRS $HOME/.config/xdg:/etc/xdg:/usr/local/etc/xdg:/usr/etc/xdg
set -gx XDG_CONFIG_HOME $HOME/.config
set -gx XDG_CURRENT_DESKTOP Hyprland
set -gx XDG_CURRENT_SESSION Hyprland
set -gx XDG_DATA_DIRS $HOME/.local/share:/nix/var/nix/profiles/default/share:/usr/local/share:/usr/share
set -gx XDG_DATA_DIRS /var/lib/flatpak/exports/share $HOME/.local/share/flatpak/exports/share $XDG_DATA_DIRS
set -gx XDG_DATA_HOME $HOME/.local/share
set -gx XDG_DESKTOP_DIR $HOME/.Desktop
set -gx XDG_DESKTOP_PORTAL_DIR /run/user/1000/xdg-desktop-portal/portals
set -gx XDG_DOCUMENTS_DIR $HOME/.Documents
set -gx XDG_DOWNLOAD_DIR $HOME/.Downloads
set -gx XDG_LIB_HOME $HOME/.local/lib
set -gx XDG_MUSIC_DIR $HOME/.Music
set -gx XDG_PICTURES_DIR $HOME/.Pictures
set -gx XDG_PUBLICSHARE_DIR $HOME/.Public
set -gx XDG_RUNTIME_DIR /run/user/1000
set -gx XDG_SESSION_DESKTOP Hyprland
set -gx XDG_SESSION_TYPE wayland
set -gx XDG_STATE_HOME $HOME/.local/state
set -gx XDG_TEMPLATES_DIR $HOME/.Templates
set -gx XDG_UTILS_DEBUG_LEVEL 3
set -gx XDG_VIDEOS_DIR $HOME/.Videos
