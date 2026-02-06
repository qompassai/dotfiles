#!/usr/bin/env bash
# /qompassai/dotfiles/.config/akvcam/frame.sh
# Qompass AI AKVCAM Default Frame Script
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
mkdir -p "$HOME/.config/akvcam" && magick -size 1920x1080 xc:blue -colorspace sRGB -depth 32 BMP3:"$HOME/.config/akvcam/default_frame.bmp" && file "$HOME/.config/akvcam/default_frame.bmp"
