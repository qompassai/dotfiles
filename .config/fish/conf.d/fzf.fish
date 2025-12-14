# /qompassai/dotfiles/.config/fish/fzf.fish
# Qompass AI Fish Fuzzy Finder (FZF) Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
if not status is-interactive && test "$CI" != true
    exit
end
set --global _fzf_search_vars_command '_fzf_search_variables (set --show | psub) (set --names | psub)'
fzf_configure_bindings
function _fzf_uninstall --on-event fzf_uninstall
    _fzf_uninstall_bindings
    set --erase _fzf_search_vars_command
    functions --erase _fzf_uninstall _fzf_migration_message _fzf_uninstall_bindings fzf_configure_bindings
    complete --erase fzf_configure_bindings
    set_color cyan
    echo "fzf.fish uninstalled."
    echo "You may need to manually remove fzf_configure_bindings from your config.fish if you were using custom key bindings."
    set_color normal
end
