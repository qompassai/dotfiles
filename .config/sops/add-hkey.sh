#!/bin/bash
# ~/.config/sops/add-hkey.sh
# ------------------------------
# Copyright (C) 2025 Qompass AI, All rights reserved

HOSTNAME="${1:-your-server.com}"
KEY_TYPE="${2:-rsa}"
SOPS_CONFIG_DIR="$HOME/.config/sops"
HOST_KEYS_DIR="$SOPS_CONFIG_DIR/host-keys"

if [[ "$HOSTNAME" == "your-server.com" ]]; then
    echo "Usage: $0 <hostname> [key_type]"
    echo "Example: $0 example.com rsa"
    exit 1
fi
mkdir -p "$HOST_KEYS_DIR"
echo "Adding host key for $HOSTNAME..."
ssh-keyscan -t "$KEY_TYPE" "$HOSTNAME" | ssh-to-pgp -o "$HOST_KEYS_DIR/$HOSTNAME.asc"
gpg --import "$HOST_KEYS_DIR/$HOSTNAME.asc"
HOST_KEY_FP=$(gpg --list-keys --with-colons "$HOSTNAME" | awk -F: '/fpr:/ {print $10}' | head -n1)
echo "Host key fingerprint for $HOSTNAME: $HOST_KEY_FP"
echo ""
echo "To use this key in SOPS, add this fingerprint to your config.yaml:"
echo "pgp: >-"
echo "  0x4F8B914D6026570F,"
echo "  $HOST_KEY_FP"
