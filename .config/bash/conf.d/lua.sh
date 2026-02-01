#!/usr/bin/env bash
# /qompassai/dotfiles/.config/bash/conf.d/lua.sh
# Qompass AI Bash Lua Config
# Copyright (C) 2026 Qompass AI, All rights reserved
# --------------------------------------------------
eval "$(fzf --bash)"
[[ $- == *i* ]] || return 0
export LUAROCKS_CONFIG="${HOME}/.config/luarocks/luarocks-5.1.lua"
lua51_lib="${lua51_root}/lib/lua/5.1"
lua51_lua="${lua51_root}/share/lua/5.1"
lua51_root="${XDG_DATA_HOME}/lua/5.1"
luajit_lib="${luajit_root}/lib/lua/5.1"
luajit_lua="${luajit_root}/share/lua/5.1"
luajit_root="${XDG_DATA_HOME}/lua/luajit"
export LUA_PATH="\
${lua51_lua}/?.lua;\
${lua51_lua}/?/init.lua;\
${luajit_lua}/?.lua;\
${luajit_lua}/?/init.lua;\
;;"
export LUA_CPATH="\
${luajit_lib}/?.so;\
${lua51_lib}/?.so;\
;;"
export PATH="/usr/bin:$HOME/.local/share/lua/luajit/bin:$PATH"
#eval "$(luarocks path)"
unset luajit_root luajit_lua luajit_lib lua51_root lua51_lua lua51_lib
export VIMRUNTIME="${XDG_DATA_HOME}/share/nvim/runtime"
