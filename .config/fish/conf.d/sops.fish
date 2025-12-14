# /qompassai/dotfiles/.config/fish/conf.d/sops.fish
# Qompass AI Fish Secret Operations (SOPs) Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
set -x SOPS_CONFIG $XDG_CONFIG_HOME/sops/.sops.yml
set -x SOPS_AGE_KEY_FILE $XDG_CONFIG_HOME/sops/age/keys.txt
