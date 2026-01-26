#!/usr/bin/env bash
# /qompassai/dotfiles/.config/bash/conf.d/ssl.sh
# Qompass AI Bash SSL Config
# Copyright (C) 2026 Qompass AI, All rights reserved
####################################################
export SSLKEYLOGFILE="$HOME/.cache/sslkeys.log"
export NSS_ALLOW_SSLKEYLOG=1
