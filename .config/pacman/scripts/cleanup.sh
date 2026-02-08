#!/usr/bin/env bash

# cleanup.sh
# Qompass AI - [ ]
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
set -e
LIMINE_CONF="/boot/limine.conf"
MACHINE_ID=$(cat /etc/machine-id)
echo "🧹 Cleaning up old kernel files..."
if [ -d "/boot/$MACHINE_ID" ]; then
    for kernel_dir in /boot/$MACHINE_ID/*/; do
        if [ -d "$kernel_dir" ]; then
            # Count files
            file_count=$(ls -1 "$kernel_dir" 2> /dev/null | wc -l)

            if [ "$file_count" -gt 4 ]; then
                echo "  Cleaning: $kernel_dir"
                # Keep newest 4 files (2 kernel + 2 initramfs)
                ls -t "$kernel_dir"* | tail -n +5 | xargs rm -f
            fi
        fi
    done
fi
"$XDG_CONFIG_HOME/pacman/scripts/limine.sh"
echo "✅ Cleanup complete"
