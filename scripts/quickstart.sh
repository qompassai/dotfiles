#!/usr/bin/env bash
# /qompassai/dotfiles/scripts/quickstart.sh
# Qompass AI Quick Start
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
REPO="https://github.com/qompassai/dotfiles"
TARGET_DIR="$HOME/.dotfiles"
if [ -d "$TARGET_DIR" ]; then
    echo "Removing existing dotfiles directory..."
    rm -rf "$TARGET_DIR"
fi
echo "Cloning Qompass AI Dotfiles..."
git clone "$REPO" "$TARGET_DIR"
echo "Setting up symlinks..."
mkdir -p "$HOME/.config/nix" "$HOME/.profile.d"
ln -sf "$TARGET_DIR/.config/nix/nix.conf" "$HOME/.config/nix/nix.conf"
ln -sf "$TARGET_DIR/.profile.d/67-nix.sh" "$HOME/.profile.d/67-nix.sh"
mkdir -p "$HOME/.config"
ln -sfn "$TARGET_DIR/home" "$HOME/.config/home" 2>/dev/null || true
ln -sfn "$TARGET_DIR/.local" "$HOME/.local" 2>/dev/null || true
ln -sf "$TARGET_DIR/flake.nix" "$HOME/.config/flake.nix" 2>/dev/null || true
source "$HOME/.profile.d/67-nix.sh" 2>/dev/null || {
    echo "WARNING: Could not source Nix profile configuration. Falling back to manual exporting"
    export NIX_CONF_DIR="$HOME/.config/nix"
    export NIX_STORE_DIR="$HOME/.nix/store"
    export NIX_STATE_DIR="$HOME/.local/state/nix"
    export NIX_LOG_DIR="$HOME/.local/state/nix/log"
    export NIX_PROFILE_DIR="$HOME/.nix-profile"
    export PATH="$NIX_PROFILE_DIR/bin:$PATH"
}
if ! command -v nix >/dev/null; then
    echo "Installing Nix with custom configuration..."
    mkdir -p /.nix/var/nix/{profiles,gcroots,db}
    chown -R "$(whoami)" /.nix
    sh <(curl -L https://nixos.org/nix/install) --daemon \
        --nix-extra-conf-file "$NIX_CONF_DIR/nix.conf"
    if [ -f './nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh' ]; then
        . '/.nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh'
    elif [ -f "$HOME/.nix-profile/etc/profile.d/nix.sh" ]; then
        . "$HOME/.nix-profile/etc/profile.d/nix.sh"
    fi
fi
echo "Setting up Nix environment..."
cd "$TARGET_DIR"
nix flake update
detect_shell() {
    case "$(ps -p $$ -o comm=)" in
    *bash*) echo "bash" ;;
    *zsh*) echo "zsh" ;;
    *fish*) echo "fish" ;;
    *) echo "bash" ;;
    esac
}
USER_SHELL=$(detect_shell)
echo "Detected shell: $USER_SHELL"
nix develop --command "$USER_SHELL"
