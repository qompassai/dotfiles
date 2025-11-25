# /qompassai/dotfiles/.config/fish/conf.d/git.fish
# Qompass AI Fish Git Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
set -gx GIT_DISCOVERY_ACROSS_FILESYSTEM 1
set -gx GIT_EDITOR nvim
set -gx GIT_PAGER nvimpager
set -gx GIT_CREDENTIAL_CACHE_TIMEOUT 3600
set -gx GIT_SSH_COMMAND "ssh -o ControlMaster=auto -o ControlPersist=600"
