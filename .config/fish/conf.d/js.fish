# /qompassai/dotfiles/.config/fish/conf.d/js.fish
# Qompass AI Javascript (JS) Fish Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
if not set -q XDG_DATA_HOME
  set -gx XDG_DATA_HOME "$HOME/.local/share"
end
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
