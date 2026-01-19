# /qompassai/dotfiles/.config/fish/conf.d/lua.fish
# Qompass AI Fish Lua Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
if not status is-interactive && test "$CI" != true
    exit
end
set --global _fzf_search_vars_command '_fzf_search_variables (set --show | psub) (set --names | psub)'
fzf_configure_bindings
function _fzf_uninstall --on-event fzf_uninstall
    if type -q _fzf_uninstall_bindings
        _fzf_uninstall_bindings
    end
    set --erase _fzf_search_vars_command
    functions --erase _fzf_uninstall _fzf_migration_message _fzf_uninstall_bindings fzf_configure_bindings
    complete --erase fzf_configure_bindings
    set_color cyan
    echo "fzf.fish uninstalled."
    echo "You may need to manually remove fzf_configure_bindings from your config.fish if you were using custom key bindings."
    set_color normal
end
if type -q luarocks
    set -l lr (luarocks --lua-version=5.1 path)
    for line in $lr
        if string match -q 'export LUA_PATH=*' $line
            set -x LUA_PATH (string replace -r "^export LUA_PATH='(.*)'" '$1' $line)
        else if string match -q 'export LUA_CPATH=*' $line
            set -x LUA_CPATH (string replace -r "^export LUA_CPATH='(.*)'" '$1' $line)
        else if string match -q 'export PATH=*' $line
            set -l newpath (string replace -r "^export PATH='(.*)'" '$1' $line)
            set -x PATH $newpath $PATH
        end
    end
end
set -x LUA_PATH "$XDG_DATA_HOME/luarocks/share/lua/5.1/?.lua;$XDG_DATA_HOME/luarocks/share/lua/5.1/?/init.lua;$LUA_PATH"
set -x LUA_CPATH "$XDG_DATA_HOME/luarocks/lib/lua/5.1/?.so;$LUA_CPATH"
