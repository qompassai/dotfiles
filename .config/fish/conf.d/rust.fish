# /qompassai/dotfiles/.config/fish/conf.d/rust.fish
# Qompass AI Fish Rust Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
set -x CARGO_HOME $HOME/.cargo
fish_add_path -P $CARGO_HOME/bin
set -x CARGO_BUILD_JOBS 8
set -x CARGO_TARGET_DIR $HOME/.cargo-target
set -x CARGO_TERM_COLOR auto
set -x RUST_BACKTRACE 1
set -x RUSTUP_HOME $HOME/.rustup
#set -x RUSTFLAGS "-C target-cpu=native -C debuginfo=1"
set -x RUSTDOCFLAGS "-C debuginfo=1"
set -x RUST_ANALYZER_LOG info
set -x SCCACHE_DIR $HOME/.cache/sccache
set -x RUSTC_WRAPPER sccache
