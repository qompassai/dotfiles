# /qompassai/dotfiles/.config/fish/conf.d/git.fish
# Qompass AI Fish Git Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
set -lx GIT_AUTHOR_NAME                 (pass show git/author)
set -lx GIT_AUTHOR_EMAIL                (pass show git/author_email)
set -lx GIT_COMMITTER_NAME              $GIT_AUTHOR_NAME
set -lx GIT_COMMITTER_EMAIL             $GIT_AUTHOR_EMAIL
set -gx GIT_CREDENTIAL_CACHE_TIMEOUT    3600
set -gx GIT_DISCOVERY_ACROSS_FILESYSTEM 1
set -gx GIT_EDITOR                      nvim
set -gx GIT_PAGER                       nvimpager
set -gx GIT_SSH_COMMAND                 "ssh -o ControlMaster=auto -o ControlPersist=600"
set -x GIT_SSL_CAINFO /etc/ssl/certs/ca-certificates.crt
set -gx GIT_TERMINAL_PROMPT             1
set -gx JJ_EDITOR                       nvim
set -gx JJ_PAGER                        nvimpager
set -gx JJ_TERMINAL_PROMPT              1

