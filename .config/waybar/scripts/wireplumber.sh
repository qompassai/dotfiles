#!/bin/bash
# /qompassai/dotfiles/.config/waybar/scripts/wireplumber.sh
# ---------------------------------------
# Copyright (C) 2025 Qompass AI, All rights reserved
volume=$(wpctl get-volume @DEFAULT_AUDIO_SINK@ | awk '{print int($2*100)}')
muted=$(wpctl get-volume @DEFAULT_AUDIO_SINK@ | grep -o "MUTED" || echo "")
if [[ $muted == "MUTED" ]]; then
    icon=""
    percentage="Muted"
else
    if [[ $volume -gt 70 ]]; then
        icon=""
    elif [[ $volume -gt 30 ]]; then
        icon=""
    else
        icon=""
    fi
    percentage="$volume%"
fi
echo "{\"text\":\"$percentage $icon\",\"percentage\":$volume,\"tooltip\":\"Volume: $percentage\"}"
