#!/usr/bin/env bash
# /qompassai/dotfiles/.config/bash/conf.d/99_path.sh
# Qompass AI Bash Path Script
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
PATH="${PATH//:$HOME\/.local\/bin/}"
PATH="${PATH#$HOME/.local/bin:}"
export PATH="$HOME/.local/bin:$PATH"
