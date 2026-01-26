#!/usr/bin/env bash
# /qompassai/dotfiles/.config/bash/conf.d/rust.sh
# Qompass AI Bash Rust Config
# Copyright (C) 2026 Qompass AI, All rights reserved
####################################################
CARGO_REGISTRY_TOKEN="$(pass show crates.io/token)"
eval "$(zoxide init bash)"
export CARGO_REGISTRY_TOKEN
