#!/usr/bin/env bash
# Qompass AI
# Copyright (C) 2026 Qompass AI, All rights reserved
# Optimized for low-latency, high-quality audio in video conferencing
# ========================================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info()
{
    echo -e "${BLUE}[INFO]${NC} $*"
}
log_success()
{
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}
log_warn()
{
    echo -e "${YELLOW}[WARN]${NC} $*"
}
log_error()
{
    echo -e "${RED}[ERROR]${NC} $*"
}

XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
BUILD_DIR="${TMPDIR:-/tmp}/pipewire-wireplumber-build-$$"
PIPEWIRE_PREFIX="$XDG_DATA_HOME/pipewire"
WIREPLUMBER_PREFIX="$XDG_DATA_HOME/wireplumber"
JOBS=$(nproc)
PIPEWIRE_REPO="https://gitlab.freedesktop.org/pipewire/pipewire.git"
WIREPLUMBER_REPO="https://gitlab.freedesktop.org/pipewire/wireplumber.git"
MESON_COMMON_FLAGS=(
    --buildtype=release
    --optimization=3
    --strip
)
PIPEWIRE_OPTIONS=(
    -Dselinux=disabled
    -Dgstreamer=enabled
    -Dgstreamer-device-provider=enabled
    -Dbluez5-codec-lc3plus=auto
    -Dbluez5-codec-ldac-dec=disabled
    -Dbluez5-codec-aptx=enabled
    -Dbluez5-codec-ldac=enabled
    -Dbluez5-codec-aac=enabled
    -Dbluez5-codec-opus=enabled
    -Dbluez5-codec-lc3=enabled
    -Dffmpeg=enabled
    -Dvulkan=enabled
    -Dvolume=enabled
    -Dpw-cat-ffmpeg=enabled
    -Dlibcamera=auto
    -Decho-cancel-webrtc=enabled
    -Dlv2=enabled
    -Dsnap=enabled
    -Dlibffado=auto
    -Dcompress-offload=enabled
    -Dopus=enabled
    -Ddocs=enabled
    -Dman=enabled
    -Dtest=disabled
    -Dexamples=enabled
)
WIREPLUMBER_OPTIONS=(
    -Dsystem-lua=true
    -Dintrospection=enabled
    #-Ddocs=true
    -Dmodules=true
    -Ddaemon=true
    -Dtools=true
    -Dsystemd=enabled
    #-Dtest=disabled
)
check_runtime_dependencies()
{
    log_info "Checking optional runtime dependencies..."

    local optional_packages=(
        "libldac:LDAC encoder support"
        "libfdk-aac:AAC codec support"
        "libfreeaptx:AptX codec support"
        "sbc:SBC codec support"
        "opus:Opus codec support"
        "libffado:FireWire audio support"
    )
    for pkg_info in "${optional_packages[@]}"; do
        IFS=: read -r pkg desc <<< "$pkg_info"
        if pacman -Qi "$pkg" &> /dev/null; then
            log_success "$pkg found - $desc"
        else
            log_warn "$pkg not found - $desc will be disabled"
            log_info "  Install with: sudo pacman -S $pkg"
        fi
    done
    echo ""
}
check_dependencies()
{
    log_info "Checking build dependencies..."
    local missing_deps=()
    local deps=(git meson ninja clang pkg-config)

    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing_deps+=("$dep")
        fi
    done
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        log_info "Install with: sudo pacman -S ${missing_deps[*]}"
        exit 1
    fi
    log_success "All build tools found"
    check_runtime_dependencies
}
cleanup()
{
    if [[ -d $BUILD_DIR ]]; then
        log_info "Cleaning up build directory..."
        rm -rf "$BUILD_DIR"
    fi
}
trap cleanup EXIT
setup_directories()
{
    log_info "Setting up build and installation directories..."
    mkdir -p "$BUILD_DIR"
    mkdir -p "$PIPEWIRE_PREFIX"
    mkdir -p "$WIREPLUMBER_PREFIX"
    log_success "Directories created"
}
clone_repo()
{
    local repo_url=$1
    local target_dir=$2
    local name=$3
    log_info "Cloning $name..."
    if [[ -d $target_dir ]]; then
        log_warn "$name directory exists, updating..."
        cd "$target_dir"
        git pull --rebase
    else
        git clone --depth=1 "$repo_url" "$target_dir"
    fi
    log_success "$name cloned/updated"
}
build_pipewire()
{
    log_info "Building PipeWire..."
    local src_dir="$BUILD_DIR/pipewire"
    local build_dir="$src_dir/build"
    clone_repo "$PIPEWIRE_REPO" "$src_dir" "PipeWire"
    cd "$src_dir"
    log_info "Configuring PipeWire with meson..."
    CC=clang CXX=clang++ meson setup \
        "${MESON_COMMON_FLAGS[@]}" \
        --prefix="$PIPEWIRE_PREFIX" \
        "${PIPEWIRE_OPTIONS[@]}" \
        "$build_dir"

    log_info "Compiling PipeWire (using $JOBS cores)..."
    meson compile -C "$build_dir" -j "$JOBS"
    log_info "Installing PipeWire to $PIPEWIRE_PREFIX..."
    meson install -C "$build_dir"
    log_success "PipeWire built and installed"
}
build_wireplumber()
{
    log_info "Building WirePlumber..."
    local src_dir="$BUILD_DIR/wireplumber"
    local build_dir="$src_dir/build"
    clone_repo "$WIREPLUMBER_REPO" "$src_dir" "WirePlumber"
    cd "$src_dir"
    export PKG_CONFIG_PATH="$PIPEWIRE_PREFIX/lib/pkgconfig:$PIPEWIRE_PREFIX/lib64/pkgconfig:${PKG_CONFIG_PATH:-}"
    log_info "Configuring WirePlumber with meson..."
    CC=clang CXX=clang++ meson setup \
        "${MESON_COMMON_FLAGS[@]}" \
        --prefix="$WIREPLUMBER_PREFIX" \
        "${WIREPLUMBER_OPTIONS[@]}" \
        "$build_dir"
    log_info "Compiling WirePlumber (using $JOBS cores)..."
    meson compile -C "$build_dir" -j "$JOBS"
    log_info "Installing WirePlumber to $WIREPLUMBER_PREFIX..."
    meson install -C "$build_dir"
    log_success "WirePlumber built and installed"
}
generate_env_script()
{
    local env_script="$XDG_DATA_HOME/pipewire-env.sh"
    log_info "Generating environment script..."
    cat > "$env_script" << 'EOF'
#!/usr/bin/env bash
# Source this file to use custom builds: source ~/.local/share/pipewire-env.sh
export XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
export PIPEWIRE_PREFIX="$XDG_DATA_HOME/pipewire"
export WIREPLUMBER_PREFIX="$XDG_DATA_HOME/wireplumber"
export PATH="$PIPEWIRE_PREFIX/bin:$WIREPLUMBER_PREFIX/bin:$PATH"
export LD_LIBRARY_PATH="$PIPEWIRE_PREFIX/lib:$PIPEWIRE_PREFIX/lib64:$WIREPLUMBER_PREFIX/lib:$WIREPLUMBER_PREFIX/lib64:${LD_LIBRARY_PATH:-}"
export PKG_CONFIG_PATH="$PIPEWIRE_PREFIX/lib/pkgconfig:$PIPEWIRE_PREFIX/lib64/pkgconfig:$WIREPLUMBER_PREFIX/lib/pkgconfig:${PKG_CONFIG_PATH:-}"
export PIPEWIRE_MODULE_DIR="$PIPEWIRE_PREFIX/lib/pipewire-0.3"
export SPA_PLUGIN_DIR="$PIPEWIRE_PREFIX/lib/spa-0.2"
export WIREPLUMBER_MODULE_DIR="$WIREPLUMBER_PREFIX/lib/wireplumber-0.5"
export PIPEWIRE_CONFIG_DIR="$PIPEWIRE_PREFIX/share/pipewire"
export WIREPLUMBER_CONFIG_DIR="$WIREPLUMBER_PREFIX/share/wireplumber"
echo "PipeWire environment loaded:"
echo "  PipeWire:    $PIPEWIRE_PREFIX"
echo "  WirePlumber: $WIREPLUMBER_PREFIX"
echo ""
echo "Run 'pipewire --version' to verify installation"
EOF
    chmod +x "$env_script"
    log_success "Environment script created: $env_script"
}
print_instructions()
{
    cat << EOF
${GREEN}╔════════════════════════════════════════════════════════════════╗
║              Build Complete!                                    ║
╚════════════════════════════════════════════════════════════════╝${NC}

${BLUE}Installation Locations:${NC}
  PipeWire:    $PIPEWIRE_PREFIX
  WirePlumber: $WIREPLUMBER_PREFIX

${BLUE}To use your custom build:${NC}
1. Source the environment script:
   ${YELLOW}source $XDG_DATA_HOME/pipewire-env.sh${NC}
2. Add to your shell config (~/.bashrc or ~/.config/fish/config.fish):
   ${YELLOW}source $XDG_DATA_HOME/pipewire-env.sh${NC}
3. Stop system PipeWire services (if running):
   ${YELLOW}systemctl --user stop pipewire.service pipewire.socket \
                         pipewire-pulse.service pipewire-pulse.socket \
                         wireplumber.service${NC}
4. Start your custom PipeWire:
   ${YELLOW}pipewire &
   wireplumber &${NC}
5. Or create systemd user units pointing to:
   ${YELLOW}$PIPEWIRE_PREFIX/bin/pipewire
   $WIREPLUMBER_PREFIX/bin/wireplumber${NC}
${BLUE}Verify installation:${NC}
   ${YELLOW}pipewire --version
   wireplumber --version${NC}
${BLUE}Build info:${NC}
   Compiler:      clang/clang++
   Optimization:  -O3 with strip
   Features:      All enabled except SELinux & LDAC decoder
${BLUE}Bluetooth Codecs Enabled:${NC}
   - LDAC encoder (install libldac for support)
   - AAC (install libfdk-aac for support)
   - AptX (install libfreeaptx for support)
   - Opus
   - LC3
   - SBC
${BLUE}To install optional codec support:${NC}
   ${YELLOW}sudo pacman -S libldac libfdk-aac libfreeaptx sbc opus${NC}
${BLUE}To rebuild later:${NC}
   ${YELLOW}$0${NC}
EOF
}
main()
{
    log_info "Starting PipeWire + WirePlumber build process"
    log_info "Build directory: $BUILD_DIR"
    check_dependencies
    setup_directories
    build_pipewire
    build_wireplumber
    generate_env_script
    log_success "Build process completed successfully!"
    print_instructions
}
main "$@"
