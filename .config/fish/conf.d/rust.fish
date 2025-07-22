set -x CARGO_HOME ~/.cargo
fish_add_path -P $CARGO_HOME/bin

# Rust Nightly build helper
function build_hpc
    cargo +nightly build --release
    or echo "Build failed. Check nightly Rust toolchain." >&2
end

