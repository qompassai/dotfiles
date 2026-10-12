#!/usr/bin/env bash

# /qompassai/dotfiles/.config/bash/conf.d/audio.sh
# Qompass AI Bash Audio Config
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
export AUDIODRIVER="pipewire"
# SOXOPTS was exported twice with different values (the second export
# silently won); merged into the single intended value.
export SOXOPTS="--buffer 131072 -V1"
