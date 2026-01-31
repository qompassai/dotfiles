# /qompassai/dotfiles/.config/fish/conf.d/34_lua.fish
# Qompass AI Fish Lua Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
if not status is-interactive && test "$CI" != true
    exit
end
set -x LUAROCKS_CONFIG "$HOME/.config/luarocks/luarocks-5.1.lua"
set -l xdg_data_home (set -q XDG_DATA_HOME && echo $XDG_DATA_HOME || echo "$HOME/.local/share")
set -l luajit_root "$xdg_data_home/lua/luajit"
set -l luajit_lua "$luajit_root/share/lua/5.1"
set -l luajit_lib "$luajit_root/lib/lua/5.1"
set -l lua51_root "$xdg_data_home/lua/5.1"
set -l lua51_lua "$lua51_root/share/lua/5.1"
set -l lua51_lib "$lua51_root/lib/lua/5.1"
set -x LUA_PATH \
    "$luajit_lua/?.lua" \
    "$luajit_lua/?/init.lua" \
    "$lua51_lua/?.lua" \
    "$lua51_lua/?/init.lua" \
    ";;"
set -x LUA_CPATH \
    "$luajit_lib/?.so" \
    "$lua51_lib/?.so" \
    ";;"
set -U fish_user_paths "$luajit_root/bin" "$lua51_root/bin" $fish_user_paths
set -gx PATH /usr/bin $HOME/.local/share/lua/luajit/bin $PATH
