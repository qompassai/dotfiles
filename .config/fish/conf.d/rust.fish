# /qompassai/dotfiles/.config/fish/conf.d/rust.fish
# Qompass AI Fish Rust Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
set -x CARGO_HOME ~/.cargo
fish_add_path -P $CARGO_HOME/bin
function build_hpc
    cargo +nightly build --release
    or echo "Build failed. Check nightly Rust toolchain." >&2
end
