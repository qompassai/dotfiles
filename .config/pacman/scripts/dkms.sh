#!/usr/bin/env bash

# dkms.sh
# Qompass AI - [ ]
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
set -e
CURRENT_KERNEL=$(uname -r)
echo "🖥️  Currently running kernel: $CURRENT_KERNEL"
LATEST_KERNEL=$(find /usr/lib/modules -maxdepth 1 -type d -name "*zen*" -printf "%f\n" | sort -V | tail -1)
if [ -z "$LATEST_KERNEL" ]; then
    echo "❌ No linux-zen kernel found in /usr/lib/modules"
    exit 1
fi
echo "🎯 Target kernel for DKMS rebuild: $LATEST_KERNEL"
if [ ! -d "/usr/lib/modules/$LATEST_KERNEL/build" ]; then
    echo "📦 Kernel headers missing, installing linux-zen-headers..."
    pacman -S --noconfirm --needed linux-zen-headers
    sleep 1
    if [ ! -d "/usr/lib/modules/$LATEST_KERNEL/build" ]; then
        echo "❌ Headers still missing for $LATEST_KERNEL"
        exit 1
    fi
fi
echo "✅ Kernel headers found at /usr/lib/modules/$LATEST_KERNEL/build"
echo "🧹 Cleaning up old DKMS builds..."
dkms status -k "$LATEST_KERNEL" 2> /dev/null | grep -E "added|built" | while IFS=, read -r module _; do
    module_name=$(echo "$module" | awk '{print $1}')
    module_ver=$(echo "$module" | awk '{print $2}')
    echo "   Removing: ${module_name}/${module_ver}"
    dkms remove -m "$module_name" -v "$module_ver" -k "$LATEST_KERNEL" 2> /dev/null || true
done
echo "🔧 Running DKMS autoinstall for $LATEST_KERNEL..."
if dkms autoinstall -k "$LATEST_KERNEL" 2>&1 | grep -v "^depmod: ERROR: fstatat"; then
    echo "✅ DKMS modules built successfully"
else
    echo "⚠️  Some DKMS modules may have failed"
fi
echo ""
echo "📋 DKMS status for $LATEST_KERNEL:"
dkms status -k "$LATEST_KERNEL" 2> /dev/null || echo "   (no modules installed)"
echo ""
echo "🔄 Updating module dependencies..."
depmod -a "$LATEST_KERNEL" 2>&1 | grep -v "^depmod: ERROR: fstatat" || true
echo ""
echo "🏗️  Rebuilding initramfs..."
mkinitcpio -p linux-zen
echo ""
echo "✅ DKMS rebuild complete for $LATEST_KERNEL"
if [ "$CURRENT_KERNEL" != "$LATEST_KERNEL" ]; then
    echo ""
    echo "⚠️  NOTE: You are running $CURRENT_KERNEL"
    echo "   DKMS modules were built for: $LATEST_KERNEL"
    echo "   Reboot to use the new kernel and modules"
fi
