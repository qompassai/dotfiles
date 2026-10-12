#!/usr/bin/env bash
# /qompassai/dotfiles/.config/bash/conf.d/nix.sh
# Qompass AI Bash Nix Config
# Copyright (C) 2026 Qompass AI, All rights reserved
####################################################
# Nix itself is provided by the system profile on this machine (no
# ~/.nix-profile or nix-daemon profile script exists to source).
# NIX_STATE_HOME was removed: it is not a variable Nix reads
# (NIX_STATE_DIR is the state directory, a different thing, owned
# by the daemon). NIX_PROFILES is real and stays, XDG-shaped.
export NIX_PROFILES="${XDG_STATE_HOME:-$HOME/.local/state}/nix/profiles"
