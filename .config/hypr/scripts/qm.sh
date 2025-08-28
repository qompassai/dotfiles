#!/bin/bash
# Qompass AI - [Add description here]
# Copyright (C) 2025 Qompass AI, All rights reserved
# ----------------------------------------

rate-mirrors --protocol=https --entry-country=US arch >/tmp/mirrors
if [ $? -eq 0 ] && grep -q '^Server' /tmp/mirrors; then
    sudo cp /tmp/mirrors /etc/pacman.d/mirrorlist
    sudo pacman -Syy
else
    echo "Failed to generate a valid mirrorlist."
fi
