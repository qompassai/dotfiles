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

if [ ! -d "$TARGET_DIR" ]; then
    git clone "$REPO" "$TARGET_DIR"
else
    echo "Dotfiles already exist at $TARGET_DIR. Updating..."
    git -C "$TARGET_DIR" pull
fi
echo "Copying configuration files..."
mkdir -p ~/.config
rsync -av --no-perms --no-owner --no-group \
    --include='home/' \
    --exclude='*' \
    "$TARGET_DIR/" "$HOME/.config/"
if [ -d "$TARGET_DIR/.local" ]; then
    echo "Copying .local directory..."
    rsync -av --no-perms --no-owner --no-group \
        "$TARGET_DIR/.local/" "$HOME/.local/"
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
        # Fallback to shell from $SHELL variable
        basename "${SHELL:-bash}"
    fi
}
USER_SHELL=$(detect_shell)
echo "Detected shell: $USER_SHELL"
nix develop --command "$USER_SHELL"
