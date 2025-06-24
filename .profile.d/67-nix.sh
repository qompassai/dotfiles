#!/usr/bin/env bash
# /qompassai/Shell/.profile.d/67-nix.sh
# Qompass AI Nix Profile.d
# # Copyright (C) 2025 Qompass AI, All rights reserved
######################################################
NIX_CONF_DIR="$HOME/.config/nix"
NIX_DATA_DIR="$HOME/.local/share/nix"
NIX_LOG_DIR="$HOME/.local/state/nix/log"
NIX_PROFILE_DIR="$HOME/.nix-profile"
NIX_STATE_DIR="$HOME/.local/state/nix"
NIX_STORE_DIR="$HOME/.nix/store"
mkdir -p "$NIX_STORE_DIR" "$NIX_STATE_DIR" "$NIX_LOG_DIR" "$NIX_CONF_DIR" "$NIX_PROFILE_DIR"
chmod 755 "$NIX_STORE_DIR"
export HYDRA_CONFIG_PATH="$HOME/.config/hydra"
export HYDRA_FULL_ERROR=1
export NIX_CFLAGS_COMPILE="-I$NIX_PROFILE_DIR/include"
export NIX_CONF_DIR
export NIX_DATA_DIR
export NIX_LOG_DIR
export NIX_PATH="nixpkgs=https://github.com/NixOS/nixpkgs/archive/nixos-unstable.tar.gz"
export NIX_PROFILE_DIR
export NIX_REMOTE="unix://${XDG_RUNTIME_DIR:-/run/user/1000}/nix/daemon-socket/socket"
export NIX_SSL_CERT_FILE="/etc/ssl/certs/ca-certificates.crt"
export NIX_STATE_DIR
export NIX_STORE_DIR
export PATH="$NIX_PROFILE_DIR/bin:$PATH"
export STACK_USE_NIX=1
