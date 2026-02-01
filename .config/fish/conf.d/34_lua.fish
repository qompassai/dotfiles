# /qompassai/dotfiles/.config/fish/conf.d/34_lua.fish
# Qompass AI Fish Lua Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
if not status is-interactive && test "$CI" != true
    exit
end
set -gx LUAROCKS_CONFIG "$HOME/.config/luarocks/luarocks-5.1.lua"
set -l xdg_data_home (set -q XDG_DATA_HOME && echo $XDG_DATA_HOME || echo "$HOME/.local/share")
set -l luajit_root "$xdg_data_home/lua/luajit"
set -l luajit_lua "$luajit_root/share/lua/5.1"
set -l luajit_lib "$luajit_root/lib/lua/5.1"
set -l lua51_root "$xdg_data_home/lua/5.1"
set -l lua51_lua "$lua51_root/share/lua/5.1"
set -l lua51_lib "$lua51_root/lib/lua/5.1"
set -gx LUA_PATH \
    "$luajit_lua/?.lua" \
    "$luajit_lua/?/init.lua" \
    "$lua51_lua/?.lua" \
    "$lua51_lua/?/init.lua" \
    ";;"
set -gx LUA_CPATH \
    "$luajit_lib/?.so" \
    "$lua51_lib/?.so" \
    ";;"
fish_add_path "$luajit_root/bin"
fish_add_path "$lua51_root/bin"
