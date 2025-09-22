# /qompassai/dotfiles/.config/fish/conf.d/js.fish
# Qompass AI Javascript (JS) Fish Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
set -gx PNPM_HOME "$XDG_DATA_HOME/pnpm"
if not string match -q -- $PNPM_HOME $PATH
  set -gx PATH "$PNPM_HOME" $PATH
end
