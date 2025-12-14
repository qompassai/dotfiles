#!/usr/bin/env bash
# /qompassai/dotfiles/.config/kernel/shsdboot.sh
# Qompass AI Systemdboot Script
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
set -e
PARTUUID="714c9eee-4984-4113-bfbd-ffb9b74f3e3e"
KVER="6.16.10-arch1-1"
EFI_DIR="/boot/EFI/6.16.10-arch1-1"
KERNEL_SRC="/boot/vmlinuz-linux"
INITRD_SRC="/boot/initramfs-linuximg"
UCODE_SRC="/boot/intel-ucode.img"
LOADER_ENTRY="/boot/loader/entries/${KVER}.conf"
sudo mkdir -p "$EFI_DIR"
sudo cp "$KERNEL_SRC" "$EFI_DIR/linux"
[ -f "$INITRD_SRC" ] && sudo cp "$INITRD_SRC" "$EFI_DIR/initrd"
[ -f "$UCODE_SRC" ] && sudo cp "$UCODE_SRC" "$EFI_DIR/intel-ucode.img"
cat <<EOF | sudo tee "$LOADER_ENTRY" >/dev/null
# Boot Loader Specification type#1 entry
title      Arch Linux $KVER
version    $KVER
sort-key   $KVER
options    root=PARTUUID=${PARTUUID} rw rootflags=subvol=@ quiet splash zswap.enabled=0 nvidia_drm.modeset=1 nvidia.NVreg_EnableGpuFirmware=0 ibt=off
linux      /EFI/${KVER}/linux
initrd     /EFI/${KVER}/intel-ucode.img
initrd     /EFI/${KVER}/initrd
EOF
echo "Copied kernel/initrd/ucode to /boot/EFI/$KVER and created loader entry."
#sha256sum /boot/vmlinuz-linux /boot/EFI/6.17.0-arch1-1/linux
#sha256sum /boot/initramfs-linux.img /boot/EFI/6.17.10-arch1-1/initrd
