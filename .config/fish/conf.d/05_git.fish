# /qompassai/dotfiles/.config/fish/conf.d/git.fish
# Qompass AI Fish Git Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
set -l author_name  (pass show git/author       2>/dev/null | string trim)
set -l author_email (pass show git/author_email 2>/dev/null | string trim)
if test -n "$author_name"
    set -lx GIT_AUTHOR_NAME    $author_name
    set -lx GIT_COMMITTER_NAME $author_name
end

if test -n "$author_email"
    set -lx GIT_AUTHOR_EMAIL    $author_email
    set -lx GIT_COMMITTER_EMAIL $author_email
end
set -lx GIT_COMMITTER_NAME          $GIT_AUTHOR_NAME
set -lx GIT_COMMITTER_EMAIL         $GIT_AUTHOR_EMAIL
set -gx GIT_CONFIG_GLOBAL           $XDG_CONFIG_HOME/git/config
set -x GIT_CREDENTIAL_CACHE_TIMEOUT    3600
set -x GIT_DISCOVERY_ACROSS_FILESYSTEM 1
set -e  GIT_EXEC_PATH
set -gx GIT_EDITOR                      nvim
set -x GIT_PAGER                       nvimpager
set -x GIT_PROTOCOL_VERSION            2
set -x GIT_SIGNINGKEY (pass show git/signk | string trim)
set -x  GIT_SSL_CAINFO /etc/ssl/certs/ca-certificates.crt
set -x GIT_TERMINAL_PROMPT             1
set -x JJ_EDITOR                       nvim
set -x JJ_PAGER                        nvimpager
set -x JJ_USER_NAME                    $GIT_AUTHOR_NAME
set -x JJ_USER_EMAIL                   $GIT_AUTHOR_EMAIL
set -x JJ_TERMINAL_PROMPT              1
set -x SOPS_AGE_KEY_FILE               $XDG_CONFIG_HOME/sops/age/keys.txt
