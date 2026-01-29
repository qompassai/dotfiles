#!/usr/bin/env bash
# /qompassai/dotfiles/.config/bash/conf.d/lua.sh
# Qompass AI Bash Lua Config
# Copyright (C) 2026 Qompass AI, All rights reserved
# --------------------------------------------------
eval "$(fzf --bash)"
#eval "$(luarocks --lua-version=5.1 path)"
#export PATH="$HOME/.local/share/lua/luajit/bin:$HOME/.local/share/lua/lua5.1/bin:$PATH"
export LUA_PATH="$HOME/.local/share/lua/share/lua/5.1/?.lua;$HOME/.local/share/lua/share/lua/5.1/?/init.lua;$HOME/.local/share/lua/luajit/share/lua/5.1/?.lua;$HOME/.local/share/lua/luajit/share/lua/5.1/?/init.lua;;"
export LUA_CPATH="$HOME/.local/share/lua/lib/lua/5.1/?.so;$HOME/.local/share/lua/luajit/lib/lua/5.1/?.so;;"
