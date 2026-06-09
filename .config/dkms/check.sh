#!/usr/bin/env bash

# check.sh
# Qompass AI - [ ]
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
set -euo pipefail

pkgs=(
    acpi_call-dkms
    akvcam-dkms
    boost174
    blackmagic
    broadcom-wl-dkms
    chipsec-dkms-git
    corefreq-dkms
    cryptodev-linux-dkms
    cuda-boost-bypass
    dm-sflc-dkms
    drbd-dkms
    droidcam-dkms
    dstep
    exanic-dkms
    fortify-headers
    gasket-dkms-git
    haxm-dkms-git
    hp_vendor-dkms
    ibdump
    kernel-mft-dkms
    kmon
    lkrg-dkms
    linux-gpib-dkms
    looking-glass-module-dkms
    mimic-bpf-dkms
    mstflint
    mtgpu-dkms
    netatop-dkms
    netfilter-fullconenat-dkms-git
    nvidia-fs-dkms
    nvidia-open-dkms
    nullfsvfs-dkms
    msi-psu-dkms
    nvidia-mft
    ovpn-dco-dkms
    pat-dealloc-dkms
    pfring-dkms
    r8125-dkms
    rapiddisk-dkms
    rtpengine-kernel-dkms
    rtw89-dkms-git
    rtw89bt-dkms-git
    scap-dkms
    scst-dkms
    smartcam-dkms
    snd-hdspe-dkms
    snd-pcsp-dkms
    snd-usb-audio-fasttrack-dkms
    tcp-brutal-dkms
    tyton-dkms-git
    util-linux-libs-aes
    virtualbox-host-dkms
    vhba-module-dkms
    vtunerc-dkms
    v4l2loopback-dkms
    v4l2loopback-dc-dkms
    winesync-dkms
    winesync-header
    wireguard-dkms
    xtables-addons-dkms
    xt_wgobfs-dkms
    zoom-l8-dkms
    zfs-dkms
)

# Map package names to actual kernel module names where they differ
declare -A modmap=(
    [acpi_call - dkms]=acpi_call
    [broadcom - wl - dkms]=wl
    [corefreq - dkms]=corefreqk
    [cryptodev - linux - dkms]=cryptodev
    [drbd - dkms]=drbd
    [droidcam - dkms]=v4l2loopback_dc
    [exanic - dkms]=exanic
    [gasket - dkms - git]=gasket
    [haxm - dkms - git]=intel_haxm
    [hp_vendor - dkms]=hp_accel
    [kernel - mft - dkms]=mft
    [lkrg - dkms]=p_lkrg
    [linux - gpib - dkms]=gpib_common
    [looking - glass - module - dkms]=kvmfr
    [mtgpu - dkms]=mtgpu
    [netatop - dkms]=netatop
    [netfilter - fullconenat - dkms - git]=xt_FULLCONENAT
    [nvidia - fs - dkms]=nvidia_fs
    [nvidia - open - dkms]=nvidia
    [nullfsvfs - dkms]=nullfsvfs
    [msi - psu - dkms]=msi-psu
    [ovpn - dco - dkms]=ovpn-dco
    [pfring - dkms]=pf_ring
    [r8125 - dkms]=r8125
    [rapiddisk - dkms]=rapiddisk
    [rtpengine - kernel - dkms]=xt_RTPENGINE
    [rtw89 - dkms - git]=rtw89pci
    [rtw89bt - dkms - git]=rtw89bt
    [scap - dkms]=scap
    [scst - dkms]=scst
    [snd - hdspe - dkms]=snd-hdspe
    [snd - pcsp - dkms]=snd-pcsp
    [snd - usb - audio - fasttrack - dkms]=snd-usb-fasttrack
    [tcp - brutal - dkms]=tcp_brutal
    [virtualbox - host - dkms]=vboxdrv
    [vhba - module - dkms]=vhba
    [vtunerc - dkms]=vtunerc
    [v4l2loopback - dkms]=v4l2loopback
    [v4l2loopback - dc - dkms]=v4l2loopback_dc
    [winesync - dkms]=winesync
    [wireguard - dkms]=wireguard
    [xtables - addons - dkms]=xt_geoip
    [xt_wgobfs - dkms]=xt_wgobfs
    [zfs - dkms]=zfs
)

for pkg in "${pkgs[@]}"; do
    case "$pkg" in
        boost174 | blackmagic | cuda-boost-bypass | dstep | fortify-headers | ibdump | kmon | mstflint | nvidia-mft | util-linux-libs-aes | winesync-header)
            echo "=== $pkg (no kernel module; skipping) ==="
            echo
            continue
            ;;
    esac

    mod="${modmap[$pkg]:-${pkg%-dkms}}"

    echo "=== $pkg (module: $mod) ==="
    if modinfo "$mod" &> /dev/null; then
        modinfo "$mod" | sed -n 's/^parm: *//p'
    else
        echo "  modinfo: no such module (maybe not built/loaded yet)"
    fi
    echo
done
