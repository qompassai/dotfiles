#!/usr/bin/env bash
set -euo pipefail
if ! command -v nix >/dev/null; then
    echo "Installing Nix package manager..."
    sh <(curl -L https://nixos.org/nix/install) --daemon
    if [ -e '/nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh' ]; then
        . '/nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh'
    fi
fi

REPO="https://github.com/qompassai/dotfiles"
TARGET_DIR="$HOME/.dotfiles"
if [ -d "$TARGET_DIR" ]; then
    echo "Removing existing dotfiles directory..."
    rm -rf "$TARGET_DIR"
fi
echo "Cloning dotfiles repository..."
git clone "$REPO" "$TARGET_DIR"
echo "Creating symlinks..."
mkdir -p "$HOME/.config"
if [ -d "$TARGET_DIR/home" ]; then
    ln -sfn "$TARGET_DIR/home" "$HOME/.config/home"
fi
if [ -d "$TARGET_DIR/.local" ]; then
    ln -sfn "$TARGET_DIR/.local" "$HOME/.local"
fi
if [ -f "$TARGET_DIR/flake.nix" ]; then
    ln -sf "$TARGET_DIR/flake.nix" "$HOME/.config/flake.nix"
fi
echo "Setting up Nix environment..."
cd "$TARGET_DIR"
nix flake update
detect_shell() {
    if [ -n "$BASH_VERSION" ]; then
        echo "bash"
    elif [ -n "$ZSH_VERSION" ]; then
        echo "zsh"
    elif [ -n "$FISH_VERSION" ]; then
        echo "fish"
    else
        basename "${SHELL:-bash}"
    fi
}
USER_SHELL=$(detect_shell)
echo "Detected shell: $USER_SHELL"
nix develop --command "$USER_SHELL"
