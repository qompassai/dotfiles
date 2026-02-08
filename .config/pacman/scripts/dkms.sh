#!/usr/bin/env bash

# dkms.sh
# Qompass AI - [ ]
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
CURRENT_KERNEL=$(uname -r)
if [[ ! $CURRENT_KERNEL =~ zen ]]; then
    echo "Not running linux-zen kernel, skipping DKMS rebuild"
    exit 0
fi
KERNEL_VERSION=${CURRENT_KERNEL%-zen}
echo "🔨 Rebuilding DKMS modules for kernel: $CURRENT_KERNEL"
if pacman -Q linux-zen-headers &> /dev/null; then
    echo "📦 Reinstalling linux-zen-headers..."
    pacman -S --noconfirm linux-zen-headers
fi
echo "🔧 Running DKMS autoinstall..."
dkms autoinstall -k "$CURRENT_KERNEL"
echo "📋 DKMS modules for $CURRENT_KERNEL:"
dkms status -k "$CURRENT_KERNEL"
echo "🏗️  Rebuilding initramfs..."
mkinitcpio -p linux-zen
echo "✅ DKMS rebuild complete"
