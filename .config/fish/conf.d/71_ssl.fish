#!/usr/bin/env fish
# /qompassai/dotfiles/.config/fish/conf.d/71_ssl.fish
# Qompass AI Fish SSL Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
set -x OPENSSL_DIR /usr
set -gx SSLKEYLOGFILE $HOME/.sslkeys.log
