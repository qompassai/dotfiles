#!/usr/bin/env sh
# /qompassai/dotfiles/.config/kernel/ukify.sh
# Qompass AI Ukify Kernel Build script
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
sudo ukify build \
        --linux /boot/vmlinuz-linux-primo \
        --initrd /boot/initramfs-linux-primo.img \
        --microcode /boot/intel-ucode.img \
        --cmdline 'root=UUID=864194e2-7a2e-4fd8-9a91-baa7c555fc37 rw' \
        --output /boot/efi/6.17.0-arch1-1/linux.efi

sudo sbsign --key ~/.sb/db.key --cert ~/.sb/db.crt \
                        --output /boot/efi/6.17.0-arch1-1/linux.efi.signed \
                        /boot/efi/6.17.0-arch1-1/linux.efi
