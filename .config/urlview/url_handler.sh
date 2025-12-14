#!/bin/bash
# /qompassai/dotfiles/.config/urlview/url_handler.sh
# Qompass AI Urlview URL Handler Script
# Copyright (C) 2025 Qompass AI, All rights reserved
#####################################################
url="$1"
if [[ -n "$DISPLAY" || -n "$WAYLAND_DISPLAY" ]]; then
    exec xdg-open "$url"
else
    case "$url" in
    mailto:*) exec neomutt "$url" ;;
    http:* | https:*) exec lynx "$url" ;;
    ftp:*) exec lynx "$url" ;;
    *)
        echo "Unsupported URL: $url"
        exit 1
        ;;
    esac
fi
