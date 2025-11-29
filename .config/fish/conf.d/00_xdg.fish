# /qompassai/dotfiles/.config/fish/conf.d/xdg.fish
# Qompass AI Fish X Desktop Group (XDG) Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
set -x INFODIR                $HOME/.local/share/info:/usr/local/share/info:/usr/share/info
set -x LANG                   en_US.UTF-8
set -x MANPATH                $HOME/.local/share/man:/usr/local/share/man:/usr/share/man
set -x PATH $PATH             $HOME/.local/bin
set -x XDG_BIN_HOME           $HOME/.local/bin:/usr/local/bin:/usr/local/sbin:/usr/bin:/usr/sbin
set -x XDG_CACHE_HOME         $HOME/.cache
set -x XDG_CONFIG_DIRS        $HOME/.config/xdg:/etc/xdg:/usr/local/etc/xdg:/usr/etc/xdg
set -x XDG_CONFIG_HOME        $HOME/.config
set -x XDG_CURRENT_DESKTOP    Hyprland
set -x XDG_CURRENT_SESSION    Hyprland
set -x XDG_DATA_DIRS          $HOME/.local/share:/nix/var/nix/profiles/default/share:/usr/local/share:/usr/share
set -x XDG_DATA_HOME          $HOME/.local/share
set -x XDG_DESKTOP_DIR        $HOME/.Desktop
set -x XDG_DESKTOP_PORTAL_DIR /run/user/1000/xdg-desktop-portal/portals
set -x XDG_DOCUMENTS_DIR      $HOME/.Documents
set -x XDG_DOWNLOAD_DIR       $HOME/.Downloads
set -x XDG_LIB_HOME           $HOME/.local/lib
set -x XDG_MUSIC_DIR          $HOME/.Music
set -x XDG_PICTURES_DIR       $HOME/.Pictures
set -x XDG_PUBLICSHARE_DIR    $HOME/.Public
set -x XDG_SESSION_DESKTOP    Hyprland
set -x XDG_SESSION_TYPE       wayland
set -x XDG_STATE_HOME         $HOME/.local/state
set -x XDG_TEMPLATES_DIR      $HOME/.Templates
set -x XDG_UTILS_DEBUG_LEVEL  3
set -x XDG_VIDEOS_DIR         $HOME/.Videos
if not set -q XDG_RUNTIME_DIR
    set -x XDG_RUNTIME_DIR "/run/user/(id -u)"
end
