#!/usr/bin/env bash
# /qompassai/dotfiles/.config/bash/conf.d/haskell.sh
# Qompass AI Bash Haskell Config
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
# ghcup was previously only sourced from ~/.profile, which bash
# never reads when ~/.bash_profile exists - so Haskell tooling was
# missing from interactive bash. Guarded, as in ~/.profile.
if [ -f "$HOME/.ghcup/env" ]; then
    # shellcheck disable=SC1091
    . "$HOME/.ghcup/env"
fi
