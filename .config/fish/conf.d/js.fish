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
