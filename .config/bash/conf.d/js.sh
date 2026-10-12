#!/usr/bin/env bash
# /qompassai/dotfiles/.config/bash/conf.d/js.sh
# Qompass AI Bash Javascript(JS) Config
# Copyright (C) 2026 Qompass AI, All rights reserved
# --------------------------------------------------
: "${XDG_CACHE_HOME:=$HOME/.cache}"
: "${XDG_CONFIG_HOME:=$HOME/.config}"
: "${XDG_DATA_HOME:=$HOME/.local/share}"
export NODE_OPTIONS="--max-old-space-size=4096"
export NPM_CONFIG_ALLOW_GIT=all
export NPM_CONFIG_CACHE="$XDG_CACHE_HOME/npm"
export NPM_CONFIG_USERCONFIG="$XDG_CONFIG_HOME/npm/npmrc"
export NVM_DIR="$XDG_DATA_HOME/nvm"
export PNPM_CONFIG_ENGINE_STRICT=false
export PNPM_HOME="$XDG_DATA_HOME/pnpm"
export npm_config_engine_strict=false
# PNPM_HOME was exported twice and its bin prepended twice (once
# unguarded, so nested shells duplicated it); one guarded prepend.
if [ -d "$PNPM_HOME" ]; then
    case ":$PATH:" in
        *":$PNPM_HOME/bin:"*) : ;;
        *) export PATH="$PNPM_HOME/bin:$PATH" ;;
    esac
fi
# nvm itself was sourced from ~/.bashrc; it belongs with the rest of
# the JavaScript environment.
if [ -r /usr/share/nvm/init-nvm.sh ]; then
    # shellcheck disable=SC1091
    . /usr/share/nvm/init-nvm.sh
fi
