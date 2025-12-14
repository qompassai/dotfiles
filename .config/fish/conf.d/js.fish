# /qompassai/dotfiles/.config/fish/conf.d/js.fish
# Qompass AI Fish Javascript (JS) Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
set -gx PNPM_HOME "$XDG_DATA_HOME/pnpm"
if not string match -q -- "$PNPM_HOME" $PATH
set -gx PATH "$PNPM_HOME" $PATH
end
if test -d "$PNPM_HOME/bin"
if not string match -q -- "$PNPM_HOME/bin" $PATH
set -gx PATH "$PNPM_HOME/bin" $PATH
end
end
set -gx NODE_PATH "$PNPM_HOME/node_modules"
set -gx NVM_DIR "$HOME/.local/share/nvm"
