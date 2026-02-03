#!/usr/bin/env bash
# /qompassai/dotfiles/.config/bash/conf.d/js.sh
# Qompass AI Bash Javascript(JS) Config
# Copyright (C) 2026 Qompass AI, All rights reserved
# --------------------------------------------------
: "${PNPM_HOME:=$XDG_DATA_HOME/pnpm}"
if [ -d "$PNPM_HOME" ]; then
    case ":$PATH:" in
        *":$PNPM_HOME:"*) : ;;
        *) PATH="$PNPM_HOME:$PATH" ;;
    esac
    export PNPM_HOME PATH
fi
export NVM_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/nvm"
export npm_config_engine_strict=false
export PNPM_CONFIG_ENGINE_STRICT=false
export NODE_OPTIONS="--max-old-space-size=4096"
