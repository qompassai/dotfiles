#!/usr/bin/env bash
DEBUG_MODE=false
DEFAULT_OS_TARGETS="linux darwin windows freebsd openbsd"
DEFAULT_ARCH_TARGETS="amd64 arm64 arm riscv64 s390x ppc64le mips64le"
BUILD_JOBS=$(nproc)
if command -v go &>/dev/null; then
  GO_VERSION=$(go version | grep -oP 'go\K[0-9]+\.[0-9]+')
  GO_MAJOR=$(echo "$GO_VERSION" | cut -d. -f1)
  GO_MINOR=$(echo "$GO_VERSION" | cut -d. -f2)
else
  GO_MAJOR=1
  GO_MINOR=24
fi
print_debug() {
  if [[ "${DEBUG_MODE}" == true ]]; then
    printf "\033[0;36m[DEBUG]\033[0m %s\n" "$1"
  fi
}
print_error() {
  printf "\033[0;31m[ERROR]\033[0m %s\n" "$1" >&2
}
print_info() {
  printf "\033[0;32m[INFO]\033[0m %s\n" "$1"
}
print_warning() {
  printf "\033[0;33m[WARN]\033[0m %s\n" "$1"
}
command_exists() {
  command -v "$1" &>/dev/null
}
check_arch_package() {
  local pkg="$1"
  if ! pacman -Q "$pkg" &>/dev/null; then
    print_warning "Package '$pkg' is not installed. Some features may not work."
    print_info "Install with: sudo pacman -S $pkg"
    return 1
  fi
  return 0
}
go_version_at_least() {
  local required_major=$1
  local required_minor=$2
  if [[ $GO_MAJOR -gt $required_major || ($GO_MAJOR -eq $required_major && $GO_MINOR -ge $required_minor) ]]; then
    return 0
  else
    return 1
  fi
}
export PATH="$HOME/.go/bin:$PATH"
export GOBIN="${GOPATH}/bin"
export GOCACHE="$HOME/.cache/go-build"
export GOENV="$HOME/.config/go/env"
export GOMODCACHE="$HOME/.cache/go-mod"
export GOPATH="${HOME}/.go"
export GVM_ROOT="$HOME/.gvm"
export PATH="$GVM_ROOT/bin:$PATH"
[[ -s "/home/$USER/.gvm/scripts/gvm" ]] && source "/home/$USER/.gvm/scripts/gvm"
export PATH="$HOME/.gvm/bin:$PATH"
if [[ ":${PATH}:" != *":${GOROOT}/bin:"* ]]; then
  export PATH="${PATH}:${GOROOT}/bin"
  print_debug "Added GOROOT/bin to PATH: ${GOROOT}/bin"
fi
if [[ ":${PATH}:" != *":${GOBIN}:"* ]]; then
  export PATH="${PATH}:${GOBIN}"
  print_debug "Added GOBIN to PATH: ${GOBIN}"
fi
export GO111MODULE="on"
export GOOS="linux"
export GOARCH="amd64"
export GOPROXY="https://proxy.golang.org,direct"
if go_version_at_least 1 21; then
  export GOSUMDB="sum.golang.org"
else
  export GOSUMDB="sum.golang.google.cn"
fi
if go_version_at_least 1 24; then
  if [ -f "go.work" ]; then
    print_debug "Go workspace file detected"
  fi
else
  if [ -f "go.work" ] && go_version_at_least 1 18; then
    export GOWORK=auto
    print_debug "Set GOWORK=auto for Go workspace support"
  fi
fi
export CGO_ENABLED=1
print_debug "Checking for required tools..."
if ! command_exists go; then
  print_error "Go is not installed. Please install Go first."
  print_info "On Arch Linux: sudo pacman -S go"
  return 1 2>/dev/null || exit 1
fi
if ! go_version_at_least 1 12; then
  print_error "This script requires Go 1.12+ (found Go $GO_MAJOR.$GO_MINOR)"
  print_info "Please upgrade Go to continue"
  return 1 2>/dev/null || exit 1
fi
#print_info "Detected Go version ${GO_MAJOR}.${GO_MINOR}"
check_arch_package "base-devel"
check_arch_package "clang"
check_arch_package "lld"
check_arch_package "llvm"
ZIG_PATH="/usr/bin/zig"
if ! command_exists zig; then
  print_warning "Zig is not installed. Zig-based cross-compilation will not be available."
  print_info "On Arch Linux: sudo pacman -S zig"
else
  print_debug "Found Zig at: $(which zig) ($(zig version))"
fi
export GO_TOOLCHAIN_CC="clang"
export GO_TOOLCHAIN_CXX="clang++"
#export CC="zig cc"
#export CXX="zig c++"
export CGO_CFLAGS="-O3 -pipe -fno-plt"
export CGO_CXXFLAGS="${CGO_CFLAGS}"
export CGO_LDFLAGS="-Wl,-O2 -Wl,--as-needed -fuse-ld=lld"
if command_exists llvm-config; then
  export LLVM_PATH="/usr/bin"
  export LLVM_CONFIG="${LLVM_PATH}/llvm-config"
  export LLVM_VERSION=$(llvm-config --version | cut -d. -f1)
  LLVM_BIN=$(llvm-config --bindir)
  if [[ ":${PATH}:" != *":${LLVM_BIN}:"* ]]; then
    export PATH="${PATH}:${LLVM_BIN}"
    print_debug "Added LLVM bin to PATH: ${LLVM_BIN}"
  fi
  export CGO_CFLAGS="$(llvm-config --cflags) ${CGO_CFLAGS}"
  export CGO_LDFLAGS="$(llvm-config --ldflags) ${CGO_LDFLAGS}"
  print_debug "LLVM version ${LLVM_VERSION} configured"
else
  print_warning "llvm-config not found. LLVM integration will be limited."
fi
install_go_tool() {
  local tool_name="$1"
  local tool_url="$2"
  local force="${3:-false}"
  if [[ "$force" == "true" ]] || ! command_exists "${tool_name}"; then
    print_info "Installing/updating ${tool_name}..."
    GOBIN="${GOBIN}" go install -v "${tool_url}" &>/dev/null
    if command_exists "${tool_name}"; then
      print_info "Successfully installed ${tool_name}"
    else
      print_error "Failed to install ${tool_name}"
      return 1
    fi
  else
    print_debug "${tool_name} is already installed"
  fi
  return 0
}
go_tools=(
  "github.com/bradfitz/apicompat@latest"                       # API compatibility checks
  "github.com/canha/golang-tools-install-script@latest"        # Tool installer
  "github.com/go-delve/delve/cmd/dlv@latest"                   # Debugger
  "github.com/go-swagger/go-swagger/cmd/swagger@latest"        # Swagger/OpenAPI codegen
  "github.com/golangci/golangci-lint/cmd/golangci-lint@latest" # Linter aggregator
  "github.com/mitchellh/gox@latest"                            # Cross-compilation
  "github.com/securego/gosec/v2/cmd/gosec@latest"              # Security scanner
  "github.com/vektra/mockery/v2@latest"                        # Mock generator for interfaces
  "golang.org/x/tools/cmd/goimports@latest"                    # Format and fix imports
  "golang.org/x/tools/gopls@latest"                            # Go language server
  "honnef.co/go/tools/cmd/staticcheck@latest"                  # Advanced static analysis
  "golang.org/x/tools/go/analysis/passes/buildssa@latest"      # SSA analysis (Go >=1.18)
  "golang.org/x/tools/cmd/gonew@latest"                        # Go project scaffolding (Go >=1.24)
  "google.golang.org/protobuf/cmd/protoc-gen-go@latest"        # Protobuf codegen
  "google.golang.org/grpc/cmd/protoc-gen-go-grpc@latest"       # gRPC codegen
  "github.com/cloudflare/circl/cmd/circl@latest"               # Post-quantum and advanced crypto tools
  "github.com/crazy-max/xgo@latest"                            # Go cross-compilation tool
  "github.com/hexops/zgo/cmd/zgo@latest"                       # Zig integration for Go
  "golang.org/x/text/cmd/gotext@latest"                        # i18n message catalog generator
  "golang.org/x/tools/cmd/stringer@latest"                     # Stringer for enum-like constants
)

if go_version_at_least 1 18; then
  go_tools+=("golang.org/x/tools/go/analysis/passes/buildssa@latest")
fi
if go_version_at_least 1 24; then
  go_tools+=("golang.org/x/tools/cmd/gonew@latest")
fi

install_zig_tools() {
  if ! command_exists zig; then
    print_warning "Zig not installed. Skipping Zig tool installation."
    return 1
  fi
  if ! command_exists zigmod; then
    print_info "Installing zigmod package manager..."
    go install github.com/nektro/zigmod/cmd/zigmod@latest
  fi
  return 0
}
install_dev_tools() {
  print_info "Installing development tools..."

  for tool in "${go_tools[@]}"; do
    tool_name=$(basename "${tool%%@*}")
    install_go_tool "${tool_name}" "${tool}"
  done
  install_zig_tools
  print_info "Development tools installation complete"
}
go_cross_simple() {
  local os="$1"
  local arch="$2"

  if [[ -z "$os" || -z "$arch" ]]; then
    print_error "Usage: go_cross_simple <os> <arch>"
    print_info "Example: go_cross_simple windows amd64"
    return 1
  fi
  if ! go tool dist list | grep -q "^${os}/${arch}$"; then
    print_warning "Unsupported OS/arch combination: ${os}/${arch}"
    print_info "To see supported combinations: go tool dist list"
    return 1
  fi
  export GOOS="$os"
  export GOARCH="$arch"
  export CGO_ENABLED=0
  print_info "Cross-compilation environment set for ${os}/${arch} (CGO disabled)"
  print_debug "GOOS=${GOOS}"
  print_debug "GOARCH=${GOARCH}"
  print_debug "CGO_ENABLED=${CGO_ENABLED}"
  trap 'export GOOS=linux GOARCH=amd64 CGO_ENABLED=1' RETURN
}
go_cross_zig() {
  local os="$1"
  local arch="$2"
  local libc="${3:-gnu}" # Default to gnu, but can specify musl

  if [[ -z "$os" || -z "$arch" ]]; then
    print_error "Usage: go_cross_zig <os> <arch> [libc]"
    print_info "Example: go_cross_zig windows amd64"
    print_info "Example: go_cross_zig linux arm64 musl"
    return 1
  fi
  if ! command_exists zig; then
    print_error "Zig is not installed. Cannot use go_cross_zig."
    print_info "Install with: sudo pacman -S zig"
    return 1
  fi
  export GOOS="$os"
  export GOARCH="$arch"
  export CGO_ENABLED=1
  local zig_target
  case "$os" in
    "linux")
      zig_target="${arch}-linux-${libc}"
      ;;
    "windows")
      zig_target="${arch}-windows"
      ;;
    "darwin")
      zig_target="${arch}-macos"
      ;;
    "freebsd")
      zig_target="${arch}-freebsd"
      ;;
    "openbsd")
      zig_target="${arch}-openbsd"
      ;;
    *)
      print_warning "Unknown OS for Zig target: $os"
      zig_target="${arch}-${os}"
      ;;
  esac
  export CC="${ZIG_PATH} cc -target ${zig_target}"
  export CXX="${ZIG_PATH} c++ -target ${zig_target}"
  if [[ "$os" == "darwin" ]]; then
    export CGO_LDFLAGS="-Wl,-O2 -Wl,-headerpad_max_install_names"
  else
    export CGO_LDFLAGS="-Wl,-O2 -Wl,--as-needed"
  fi
  if go_version_at_least 1 24; then
    :
  fi
  print_debug "Zig target: ${zig_target}"
  print_debug "CC=${CC}"
  print_debug "CXX=${CXX}"
  trap 'export CC="clang" CXX="clang++" GOOS=linux GOARCH=amd64 CGO_ENABLED=1 CGO_LDFLAGS="-Wl,-O2 -Wl,--as-needed -fuse-ld=lld"' RETURN
}
print_go_cross_help() {
  cat <<EOF
Go Cross-Compilation Tools Usage:
For pure Go packages (no CGO):
  go_cross_simple <os> <arch>
  Examples: go_linux_amd64, go_windows_amd64, go_darwin_arm64
For packages with CGO using Zig:
  go_cross_zig <os> <arch> [libc]
  Examples: go_linux_amd64_cgo, go_windows_amd64_cgo
For packages with CGO using LLVM:
  go_cross_llvm <os> <arch>
  Examples: go_linux_amd64_llvm, go_windows_amd64_llvm
Multi-platform builds:
  build_all [package] [output] [os_list] [arch_list]
  build_all_cgo [package] [output] [os_list] [arch_list]
To see supported platform combinations:
  go tool dist list
EOF
}
print_debug "Go version: $(go version)"
print_debug "GOROOT: ${GOROOT}"
print_debug "GOPATH: ${GOPATH}"
print_debug "GOBIN: ${GOBIN}"
