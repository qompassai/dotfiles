#!/usr/bin/env bash
# fix.sh
# Qompass AI
# Copyright (C) 2026 Qompass AI, All rights reserved
PRESET_FILE="/etc/mkinitcpio.d/linux-zen.preset"
BACKUP_FILE="/tmp/linux-zen.preset.backup"
if [ -f "$BACKUP_FILE" ]; then
    cp "$BACKUP_FILE" "$PRESET_FILE"
    rm "$BACKUP_FILE"
fi
rm -f /etc/mkinitcpio.d/linux-zen-primo.preset
cat > "$PRESET_FILE" << 'EOF'
# mkinitcpio preset file for the "linux-zen" package
ALL_config="/etc/mkinitcpio.conf"
ALL_kver="/boot/vmlinuz-linux-zen"
PRESETS=("default" "fallback")
default_config="/etc/mkinitcpio.conf"
default_image="/boot/initramfs-linux-zen.img"
default_options=""
fallback_config="/etc/mkinitcpio.conf"
fallback_image="/boot/initramfs-linux-zen-fallback.img"
fallback_options="-S autodetect"
EOF
rm -f /boot/vmlinuz-linux-zen-primo
rm -f /boot/initramfs-linux-zen-primo.img
rm -f /boot/initramfs-linux-zen-primo-fallback.img
if [ -d /boot/loader/entries ]; then
    # Update boot entries to use correct naming
    find /boot/loader/entries -name "*linux-zen*.conf" -exec sed -i 's/linux-zen-primo/linux-zen/g' {} \;
fi
mkinitcpio -p linux-zen
echo "✅ linux-zen preset fixed and initramfs rebuilt"
