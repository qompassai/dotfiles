#!/usr/bin/env bash
# /qompassai/dotfiles/.config/sops/add-agekey.sh
# Qompass AI Age Key Setup
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################

set -euo pipefail
HOSTNAME="${1:-}"
SSH_KEY_TYPE="${2:-ed25519}"
SOPS_CONFIG_DIR="$HOME/.config/sops"
HOST_KEYS_DIR="$SOPS_CONFIG_DIR/age-host-keys"
AGE_RECIPIENTS_FILE="$SOPS_CONFIG_DIR/age/recipients.txt"
if [[ -z "$HOSTNAME" ]]; then
	echo "Usage: $0 <hostname> [ssh_key_type]"
	echo "Example: $0 host.qompass.ai ed25519"
	exit 1
fi
mkdir -p "$HOST_KEYS_DIR"
mkdir -p "$(dirname "$AGE_RECIPIENTS_FILE")"
echo " Scanning $SSH_KEY_TYPE key from $HOSTNAME..."
ssh-keyscan -t "$SSH_KEY_TYPE" "$HOSTNAME" 2>/dev/null | tee "$HOST_KEYS_DIR/${HOSTNAME}.pub"
if ! command -v age-plugin-ssh >/dev/null 2>&1; then
	echo "❌ age-plugin-ssh not found. Please install from https://github.com/FiloSottile/age-plugin-ssh"
	exit 1
fi
echo "🔧 Converting to age recipient..."
AGE_RECIPIENT=$(age-plugin-ssh -r "$(<"$HOST_KEYS_DIR/${HOSTNAME}.pub")")
echo "✅ age recipient for $HOSTNAME:"
echo "$AGE_RECIPIENT"
echo
if [[ ! -f "$AGE_RECIPIENTS_FILE" ]] || ! grep -q "$AGE_RECIPIENT" "$AGE_RECIPIENTS_FILE"; then
	echo "$AGE_RECIPIENT" >>"$AGE_RECIPIENTS_FILE"
	echo "➕ Added to $AGE_RECIPIENTS_FILE"
fi
echo ""
echo "📌 You can now add this to your ~/.sops.yaml:"
echo
echo "creation_rules:"
echo "encrypt_all: true"
echo "  - path_regex: '.*'"
echo "    age:"
echo "      - \"$AGE_RECIPIENT\""
