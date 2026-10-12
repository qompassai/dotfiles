#!/usr/bin/env bash
# /qompassai/dotfiles/.config/bash/conf.d/ssl.sh
# Qompass AI Bash SSL Config
# Copyright (C) 2026 Qompass AI, All rights reserved
####################################################
# TLS session keys are logged for Wireshark-style analysis; the
# path now goes through XDG_CACHE_HOME instead of a hardcoded
# $HOME/.cache.
export NSS_ALLOW_SSLKEYLOG=1
export SSLKEYLOGFILE="${XDG_CACHE_HOME:-$HOME/.cache}/sslkeys.log"
