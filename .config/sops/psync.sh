#!/usr/bin/env bash
# psync.sh
# Qompass AI - [Add description here]
# Copyright (C) 2025 Qompass AI, All rights reserved
# ----------------------------------------
set -euo pipefail

REMOTE_HOST="${1:-}"
REMOTE_USER="${2:-$USER}"
REMOTE_PORT="${3:-22}"
SRC_PASS="$HOME/.password-store"
DEST_PASS="$REMOTE_USER@$REMOTE_HOST:$SRC_PASS"
SRC_AGE="$HOME/.config/sops/age/keys.txt"
DEST_AGE="$REMOTE_USER@$REMOTE_HOST:$SRC_AGE"
if [[ -z "$REMOTE_HOST" ]]; then
	echo "Usage: $0 <remote_host> [remote_user] [port]"
	exit 1
fi
echo "🔄 Syncing pass store from $SRC_PASS to $DEST_PASS ..."
scp -P "$REMOTE_PORT" -r "$SRC_PASS" "$DEST_PASS"
if [[ -f "$SRC_AGE" ]]; then
	echo "🔄 Copying age key from $SRC_AGE to $DEST_AGE ..."
	scp -P "$REMOTE_PORT" "$SRC_AGE" "$DEST_AGE"
	echo "🔒 Setting permissions on remote age key ..."
	ssh -p "$REMOTE_PORT" "$REMOTE_USER@$REMOTE_HOST" "chmod 600 $SRC_AGE"
else
	echo "⚠️  No age key found at $SRC_AGE, skipping age key sync."
fi
echo "✅ Sync complete!"
