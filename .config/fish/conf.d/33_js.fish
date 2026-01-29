# /qompassai/dotfiles/.config/fish/conf.d/js.fish
# Qompass AI Fish Javascript (JS) Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
set -gx PNPM_HOME "$XDG_DATA_HOME/pnpm"
if not string match -q -- $PNPM_HOME $PATH
    set -gx PATH $PNPM_HOME $PATH
end
set -gx NODE_PATH "$PNPM_HOME/node_modules"
set -gx nvm_data "$XDG_DATA_HOME/nvm"
set -gx BUN_INSTALL "$XDG_DATA_HOME/bun"
if not string match -q -- "$BUN_INSTALL/bin" $PATH
    set -gx PATH "$BUN_INSTALL/bin" $PATH
end
set -gx DENO_INSTALL_ROOT "$XDG_DATA_HOME/deno"
if not string match -q -- "$DENO_INSTALL_ROOT/bin" $PATH
    set -gx PATH "$DENO_INSTALL_ROOT/bin" $PATH
end
 set -gx PATH "$HOME/.local/npm-global/bin" $PATH
 set --query nvm_mirror || set --global nvm_mirror https://nodejs.org/dist
set --query nvm_data || set --global nvm_data $XDG_DATA_HOME/nvm
function _nvm_install --on-event nvm_install
    test ! -d $nvm_data && command mkdir -p $nvm_data
    echo "Downloading the Node distribution index..." 2>/dev/null
    _nvm_index_update
end
function _nvm_update --on-event nvm_update
    set --query --universal nvm_data && set --erase --universal nvm_data
    set --query --universal nvm_mirror && set --erase --universal nvm_mirror
    set --query nvm_mirror || set --global nvm_mirror https://nodejs.org/dist
end
function _nvm_uninstall --on-event nvm_uninstall
    command rm -rf $nvm_data
    set --query nvm_current_version && _nvm_version_deactivate $nvm_current_version
    set --names | string replace --filter --regex -- "^nvm" "set --erase nvm" | source
    functions --erase (functions --all | string match --entire --regex -- "^_nvm_")
end
if status is-interactive && set --query nvm_default_version && ! set --query nvm_current_version
    nvm use --silent $nvm_default_version
end
