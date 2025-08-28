#!/usr/bin/env bash
# ~/qompassai/dotfiles/.config/unbound/rotate.sh
# Copyright (C) 2025 Qompass AI, All rights reserved
# --------------------------------------------------
KEYS_DIR="/home/$USER/.config/unbound/ssl"
OLD_KEY="$KEYS_DIR/session-tickets-old.key"
NEW_KEY="$KEYS_DIR/session-tickets-new.key"
dd if=/dev/random bs=1 count=80 of="$NEW_KEY" 2>/dev/null
echo "tls-session-ticket-keys: \"$NEW_KEY\"" > /tmp/ticket-config
echo "tls-session-ticket-keys: \"$OLD_KEY\"" >> /tmp/ticket-config
chmod 600 "$NEW_KEY"
chown unbound:unbound "$NEW_KEY"
echo "New session ticket key generated. Update your unbound.conf with:"
cat /tmp/ticket-config
