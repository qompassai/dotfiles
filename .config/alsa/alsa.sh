#!/usr/bin/env bash
# /qompassai/dotfiles/.config/alsa/alsa.sh
# Qompass AI Alsa Setup Script
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
mkdir -p "$XDG_CONFIG_HOME/alsa"
alsactl -f "$XDG_CONFIG_HOME/alsa/asound.state" store
alsactl -G "$XDG_CONFIG_HOME/alsa/card-group.state" store 2> /dev/null || true
ls -lh "$XDG_CONFIG_HOME/alsa/"
head -30 "$XDG_CONFIG_HOME/alsa/asound.state"
