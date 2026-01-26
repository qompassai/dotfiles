#!/usr/bin/env bash
# /qompassai/dotfiles/.config/bash/conf.d/git.sh
# Qompass AI Bash Git Config
# Copyright (C) 2026 Qompass AI, All rights reserved
# --------------------------------------------------
GIT_AUTHOR_EMAIL="$(pass show git/author_email)"
GIT_AUTHOR_NAME="$(pass show git/author)"
GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"
GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME"
GIT_CONFIG_GLOBAL="${XDG_CONFIG_HOME:-$HOME/.config}/git/config"
GIT_CREDENTIAL_CACHE_TIMEOUT=3600
GIT_DISCOVERY_ACROSS_FILESYSTEM=1
GIT_EDITOR=nvim
GIT_LFS_SKIP_SMUDGE=1
GIT_OPTIONAL_LOCKS=0
GIT_PAGER=nvimpager
GIT_PROTOCOL_VERSION=2
GIT_SIGNINGKEY="$(pass show git/signk | xargs echo -n)"
GIT_SSH_COMMAND='ssh -o ControlMaster=auto -o ControlPersist=600'
GIT_SSL_CAINFO=/etc/ssl/certs/ca-certificates.crt
GIT_TERMINAL_PROMPT=1
JJ_EDITOR=nvim
JJ_PAGER=nvimpager
JJ_TERMINAL_PROMPT=1
SSH_AUTH_SOCK="${XDG_RUNTIME_DIR}/ssh-agent.socket"
SOPS_AGE_KEY_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/sops/age/keys.txt"
export \
  GIT_AUTHOR_EMAIL \
  GIT_AUTHOR_NAME \
  GIT_COMMITTER_EMAIL \
  GIT_COMMITTER_NAME \
  GIT_CONFIG_GLOBAL \
  GIT_CREDENTIAL_CACHE_TIMEOUT \
  GIT_DISCOVERY_ACROSS_FILESYSTEM \
  GIT_EDITOR \
  GIT_LFS_SKIP_SMUDGE \
  GIT_OPTIONAL_LOCKS \
  GIT_PAGER \
  GIT_PROTOCOL_VERSION \
  GIT_SIGNINGKEY \
  GIT_SSH_COMMAND \
  GIT_SSL_CAINFO \
  GIT_TERMINAL_PROMPT \
  JJ_EDITOR \
  JJ_PAGER \
  JJ_TERMINAL_PROMPT \
  SOPS_AGE_KEY_FILE \
  SSH_AUTH_SOCK
