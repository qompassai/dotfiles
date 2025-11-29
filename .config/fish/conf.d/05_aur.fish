# /qompassai/dotfiles/.config/fish/conf.d/05_aur.fish
# Qompass AI Fish Arch User Repository (AUR) Config
# Copyright (C) 2025 Qompass AI, All rights reserved
# ---------------------------------------------------
function yay
    sed -E 's#//.*$##' $XDG_CONFIG_HOME/yay/config.jsonc | sed '/^[[:space:]]*$/d' > $XDG_CONFIG_HOME/yay/config.json
    command yay $argv
end
