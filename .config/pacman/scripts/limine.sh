#!/usr/bin/env bash

# limine.sh
# Qompass AI - [ ]
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
set -e
ESP_MOUNT=$(findmnt -no TARGET /boot)
ESP_DEVICE=$(findmnt -no SOURCE /boot)
echo "🔧 Reinstalling Limine bootloader..."
echo "   ESP: $ESP_DEVICE mounted at $ESP_MOUNT"
echo "📦 Copying Limine files..."
mkdir -p /boot/EFI/limine
mkdir -p /boot/EFI/BOOT
cp /usr/share/limine/BOOTX64.EFI /boot/EFI/BOOT/
cp /usr/share/limine/limine-bios.sys /boot/
cp /usr/share/limine/limine-uefi-cd.bin /boot/ 2> /dev/null || true
if [ -f /usr/share/limine/BOOTX64.EFI ]; then
    cp /usr/share/limine/BOOTX64.EFI /boot/EFI/limine/limine_x64.efi
fi
DISK=$(lsblk -no PKNAME "$ESP_DEVICE" | head -1)
if [ -n "$DISK" ] && [ -b "/dev/$DISK" ]; then
    echo "💾 Installing Limine to /dev/$DISK"
    limine bios-install "/dev/$DISK" 2> /dev/null || echo "⚠️  BIOS install skipped (UEFI only?)"
fi
echo "✅ Limine bootloader reinstalled"
