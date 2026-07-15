#!/usr/bin/env bash
# /qompassai/dotfiles/.config/bash/conf.d/js.sh
# Qompass AI Bash Javascript(JS) Config
# Copyright (C) 2026 Qompass AI, All rights reserved
# --------------------------------------------------
: "${XDG_DATA_HOME:=$HOME/.local/share}"
export PNPM_HOME="$XDG_DATA_HOME/pnpm"
if [ -d "$PNPM_HOME" ]; then
    case ":$PATH:" in
        *":$PNPM_HOME/bin:"*) : ;;
        *) PATH="$PNPM_HOME/bin:$PATH" ;;
    esac
fi
export NVM_DIR="$XDG_DATA_HOME/nvm"
export npm_config_engine_strict=false
export PNPM_CONFIG_ENGINE_STRICT=false
export NODE_OPTIONS="--max-old-space-size=4096"
export PNPM_HOME="$XDG_DATA_HOME/pnpm"
export PATH="$PNPM_HOME/bin:$PATH"
