#!/usr/bin/env bash

# cleanup.sh
# Qompass AI - [ ]
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
set -e
echo "🧹 Cleaning up old kernel files..."
echo "🗑️  Removing DKMS modules for deleted kernels..."
for kver in $(dkms status 2> /dev/null | grep -oP '(?<=, )[^,]+(?=,)' | sort -u); do
    if [ ! -d "/usr/lib/modules/$kver" ]; then
        echo "   Cleaning: $kver"
        dkms status -k "$kver" 2> /dev/null | while IFS=, read -r module _; do
            module_name=$(echo "$module" | awk '{print $1}')
            module_ver=$(echo "$module" | awk '{print $2}')
            dkms remove -m "$module_name" -v "$module_ver" -k "$kver" --all 2> /dev/null || true
        done
    fi
done
if [ -f /home/phaedrus/.config/pacman/scripts/limine.sh ]; then
    /home/phaedrus/.config/pacman/scripts/limine.sh
fi

echo "✅ Cleanup complete"
