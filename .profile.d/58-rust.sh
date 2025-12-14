#!/usr/bin/env bash
# /qompassai/Shell/.profile.d/58-rust.sh
# -----------------------------
# Copyright (C) 2025 Qompass AI, All rights reserved

if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
  if [[ -n "${RUST_LOADED}" ]]; then
    return 0
  fi
fi
DEBUG_MODE=false
SUCCESS_COUNT=0
FAILED_COMPONENTS=()
CHECK_NAMES=()
check_status() {
  local name="$1" status="$2"
  CHECK_NAMES+=("$name")
  [[ "$status" == "success" ]] && ((SUCCESS_COUNT++)) || FAILED_COMPONENTS+=("$name")
}
debug_print() {
  [[ "$DEBUG_MODE" == true ]] && echo "[DEBUG] $*"
}
set_rust_target() {
  local target="${1:-x86_64-unknown-linux-gnu}"
  export CARGO_BUILD_TARGET="$target"
  debug_print "Set Rust build target to $target"
}
case ":$PATH:" in
  *":$HOME/.cargo/bin:"*) ;;
  *) export PATH="$HOME/.cargo/bin:$PATH" ;;
esac
export CARGO_PROFILE_RELEASE_LTO="thin"
export CARGO_TARGET_DIR="${HOME}/.target-cross"
#export CC="zig cc"
#export CXX="zig c++"
export CFLAGS="-fPIC -Wno-unused-command-line-argument"
export CXXFLAGS="-fPIC -Wno-unused-command-line-argument"
export FALLBACK_CC="clang"
export FALLBACK_CXX="clang++"
export GCC_CC="gcc"
export GCC_CXX="g++"
export RUST_BACKTRACE=1
export RUST_LOADED=1
export RUST_WAYLAND_CLIENT_LIBS="/usr/lib/libwayland-client.so"
export RUST_WAYLAND_SCANNER="/usr/bin/wayland-scanner"
export SCCACHE_CACHE_SIZE="50G"
export SCCACHE_DIR="$HOME/.cache/sccache"
export SCCACHE_IDLE_TIMEOUT=0
case ":$PATH:" in
  *":$HOME/.cargo/bin:"*) ;;
  *) export PATH="$HOME/.cargo/bin:$PATH" ;;
esac
for tool in cargo clippy-driver rust-analyzer rustc rustup; do
  if command -v "${tool}" &>/dev/null; then
    check_status "tool:${tool}" "success"
    debug_print "Found ${tool}"
  else
    check_status "tool:${tool}" "failed"
    debug_print "Missing ${tool}"
  fi
done
if command -v rustc &>/dev/null && command -v cargo &>/dev/null; then
  check_status "rustc_and_cargo_in_path" "success"
  debug_print "Rust and Cargo paths found"
else
  check_status "rustc_and_cargo_in_path" "failed"
  debug_print "Rust and Cargo paths not found"
fi
if [[ -d "${HOME}/.rustup/toolchains" ]]; then
  export PATH="${HOME}/.rustup/toolchains:${PATH}"
  check_status "rustup_toolchains_dir" "success"
  debug_print "Added rustup to PATH"
else
  check_status "rustup_toolchains_dir" "failed"
  debug_print "rustup toolchains dir not found"
fi
if [[ -f "${HOME}/.cargo/env" ]]; then
  . "${HOME}/.cargo/env"
  check_status "cargo_env" "success"
  debug_print "Sourced Cargo environment"
else
  check_status "cargo_env" "failed"
  debug_print "Cargo environment file not found"
fi
RUST_SYSROOT=$(rustc --print sysroot 2>/dev/null)
RUST_SRC_PATH="${RUST_SYSROOT}/lib/rustlib/src/rust"
if [[ -d "${RUST_SRC_PATH}" ]]; then
  export RUST_SRC_PATH
  check_status "rust_src_path" "success"
  debug_print "Found rust-src component"
else
  check_status "rust_src_path" "failed"
  debug_print "rust-src component not found"
fi
if command -v zoxide &>/dev/null; then
  if eval "$(zoxide init bash)"; then
    check_status "zoxide_init" "success"
    debug_print "Zoxide initialized"
  else
    check_status "zoxide_init" "failed"
    debug_print "Zoxide failed to initialize"
  fi
else
  check_status "zoxide_bin" "failed"
  debug_print "Zoxide not found"
fi
TOTAL_COMPONENTS=${#CHECK_NAMES[@]}

if [[ "${DEBUG_MODE}" == true ]]; then
  if [[ "${SUCCESS_COUNT}" -eq "${TOTAL_COMPONENTS}" ]]; then
    printf "Rust environment successfully loaded.\n"
  else
    printf "Rust environment partially loaded. Failed components: %s\n" "${FAILED_COMPONENTS[*]}"
  fi
fi
