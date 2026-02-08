#!/usr/bin/env bash

# update.sh
# Qompass AI - [ ]
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
set -e
LIMINE_CONF="/boot/limine.conf"
LIMINE_CONF_BACKUP="/boot/limine.conf.backup"
MACHINE_ID=$(cat /etc/machine-id)

cp "$LIMINE_CONF" "$LIMINE_CONF_BACKUP"

echo "🔄 Updating Limine configuration..."

if [ -f /boot/vmlinuz-linux-zen ]; then
    ZEN_VERSION=$(pacman -Q linux-zen 2> /dev/null | awk '{print $2}' || echo "unknown")
    ZEN_KERNEL_VERSION=$(file /boot/vmlinuz-linux-zen | grep -oP 'version \K[^ ]+' || echo "unknown")
fi

if [ -f /boot/vmlinuz-linux ]; then
    LINUX_VERSION=$(pacman -Q linux 2> /dev/null | awk '{print $2}' || echo "unknown")
    LINUX_KERNEL_VERSION=$(file /boot/vmlinuz-linux | grep -oP 'version \K[^ ]+' || echo "unknown")
fi

ROOT_UUID=$(findmnt -no UUID /)
CRYPT_UUID="b0fe57d3-f3a4-4915-8c0e-4060f94ad44c"

# Build kernel command line
KERNEL_CMDLINE="cryptdevice=UUID=${CRYPT_UUID}:root root=/dev/mapper/root zswap.enabled=0 rootflags=subvol=@ rw rootfstype=btrfs"

# Regenerate config
cat > "$LIMINE_CONF" << EOF
timeout: 5

/Arch Linux (linux-zen)
    protocol: linux
    kernel_path: boot():/vmlinuz-linux-zen
    kernel_cmdline: ${KERNEL_CMDLINE}
    module_path: boot():/initramfs-linux-zen.img

/Arch Linux (linux-zen fallback)
    protocol: linux
    kernel_path: boot():/vmlinuz-linux-zen
    kernel_cmdline: ${KERNEL_CMDLINE}
    module_path: boot():/initramfs-linux-zen-fallback.img

EOF

# Add BLS entries if they exist
if [ -d "/boot/$MACHINE_ID" ]; then
    cat >> "$LIMINE_CONF" << EOF
/+Arch Linux
comment: Arch Linux
comment: machine-id=$MACHINE_ID order-priority=50 
EOF

    # Add linux-zen BLS entry
    if [ -d "/boot/$MACHINE_ID/linux-zen" ]; then
        ZEN_VMLINUZ=$(find /boot/$MACHINE_ID/linux-zen -name 'vmlinuz-linux-zen*' -type f 2> /dev/null | sort -V | tail -1)
        ZEN_INITRD=$(find /boot/$MACHINE_ID/linux-zen -name 'initramfs-linux-zen-[0-9]*' -type f 2> /dev/null | sort -V | tail -1)

        if [ -n "$ZEN_VMLINUZ" ] && [ -n "$ZEN_INITRD" ]; then
            ZEN_VMLINUZ_NAME=$(basename "$ZEN_VMLINUZ")
            ZEN_INITRD_NAME=$(basename "$ZEN_INITRD")

            cat >> "$LIMINE_CONF" << EOF
  //linux-zen
  comment: ${ZEN_KERNEL_VERSION}
  protocol: linux
  module_path: boot():/$MACHINE_ID/linux-zen/$ZEN_INITRD_NAME
  path: boot():/$MACHINE_ID/linux-zen/$ZEN_VMLINUZ_NAME
  cmdline: ${KERNEL_CMDLINE}

EOF
        fi
    fi

    # Add linux BLS entry
    if [ -d "/boot/$MACHINE_ID/linux" ]; then
        LINUX_VMLINUZ=$(find /boot/$MACHINE_ID/linux -name 'vmlinuz-linux-[0-9]*' -type f 2> /dev/null | sort -V | tail -1)
        LINUX_INITRD=$(find /boot/$MACHINE_ID/linux -name 'initramfs-linux-[0-9]*' -type f 2> /dev/null | sort -V | tail -1)

        if [ -n "$LINUX_VMLINUZ" ] && [ -n "$LINUX_INITRD" ]; then
            LINUX_VMLINUZ_NAME=$(basename "$LINUX_VMLINUZ")
            LINUX_INITRD_NAME=$(basename "$LINUX_INITRD")

            cat >> "$LIMINE_CONF" << EOF
  //linux
  comment: ${LINUX_KERNEL_VERSION}
  protocol: linux
  module_path: boot():/$MACHINE_ID/linux/$LINUX_INITRD_NAME
  path: boot():/$MACHINE_ID/linux/$LINUX_VMLINUZ_NAME
  cmdline: ${KERNEL_CMDLINE}

EOF
        fi
    fi
fi

# Add other boot options
cat >> "$LIMINE_CONF" << 'EOF'
/Linux Boot Manager
comment: Linux Boot Manager
comment: order-priority=20 
protocol: efi
path: guid(ed9b3edc-684b-437f-9519-72826a16436c):/EFI/systemd/systemd-bootx64.efi

/Limine
comment: Limine
comment: order-priority=20 
protocol: efi
path: boot():/EFI/limine/limine_x64.efi

/UEFI OS
comment: UEFI OS
comment: order-priority=20 
protocol: efi
path: boot():/EFI/BOOT/BOOTX64.EFI

/EFI fallback
comment: Default EFI loader
comment: order-priority=10 
protocol: efi
path: boot():/EFI/BOOT/BOOTX64.EFI
EOF

echo "✅ Limine configuration updated"
echo "📋 Current entries:"
grep -E "^/(Arch Linux|Linux Boot Manager|Limine|UEFI OS|EFI fallback)" "$LIMINE_CONF" | sed 's/^/  /'
