#!/usr/bin/env bash
# /qompassai/dotfiles/.config/bash/conf.d/rust.sh
# Qompass AI Bash Rust Config
# Copyright (C) 2026 Qompass AI, All rights reserved
####################################################
# Reference: https://rust-lang.github.io/rustup
CARGO_REGISTRY_TOKEN="$(pass show crates.io/token)"
eval "$(zoxide init bash)"
export CARGO_HOME="${XDG_DATA_HOME:-$HOME/.local/share}/cargo"
export CARGO_REGISTRY_TOKEN
export PATH="$PATH:$HOME/.cargo/bin"
export RUSTUP_AUTO_INSTALL="1"
export RUSTUP_CONCURRENT_DOWNLOADS="4"
export RUSTUP_DIST_SERVER="https://static.rust-lang.org"
export RUSTUP_DOWNLOAD_TIMEOUT="300"
export RUSTUP_HARDLINK_PROXIES="1"
export RUSTUP_LOG="rustup=DEBUG"
export RUSTUP_HOME="${XDG_DATA_HOME:-$HOME/.local/share}/rustup"
export RUSTUP_IO_THREADS="4"
export RUSTUP_NO_BACKTRACE="0"
export RUSTUP_PERMIT_COPY_RENAME="1"
#export RUSTSEC_SCAN_MODE="deny"
export RUSTUP_TERM_COLOR="auto"
export RUSTUP_TERM_PROGRESS_WHEN="auto"
export RUSTUP_TERM_WIDTH="120"
export RUSTUP_UNPACK_RAM="1073741824"
export RUSTUP_UPDATE_ROOT="https://static.rust-lang.org/rustup"
