#!/usr/bin/env bash
# ~/.config/waybar/scripts/temp_f.sh
# ----------------------------------
# Copyright (C) 2025 Qompass AI, All rights reserved

C_PATH="/sys/class/thermal/thermal_zone0/temp"

if [[ ! -f "$C_PATH" ]]; then
    echo '{"text": "N/A ⚠", "class": "disconnected"}'
    exit 1
fi

raw_temp=$(<"$C_PATH")
celsius=$(echo "scale=1; $raw_temp / 1000" | bc)
fahrenheit=$(echo "scale=1; ($celsius * 9 / 5) + 32" | bc)

icon=""
temp_class="cool"

if (( $(echo "$fahrenheit >= 90" | bc -l) )); then
    icon=""
    temp_class="critical"
elif (( $(echo "$fahrenheit >= 75" | bc -l) )); then
    icon=""
    temp_class="warm"
fi

echo "{\"text\": \"${fahrenheit}°F $icon\", \"class\": \"$temp_class\"}"
