#!/usr/bin/env bash
# /qompassa/dotfiles/.config/dkms/dkms.sh
# Qompass AI DKMS Script
# Copyright (C) 2025 Qompass AI, All rights reserved
# ----------------------------------------
PKGS=(acpi_call-dkms
	akvcam-dkms
	blackmagic
	broadcom-wl-dkms
	chipsec-dkms-git
	corefreq-dkms
	cryptodev-linux-dkms
	drbd-dkms
	droidcam-dkms
	dm-sflc-dkms
	exanic-dkms
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
	pfring-dkms
	r8125-dkms
	rapiddisk-dkms
	rtpengine-kernel-dkms
	rtw89-dkms-git
	rtw89bt-dkms-git
	scap-dkms
	smartcam-dkms
	snd-hdspe-dkms
	snd-pcsp-dkms
	snd-usb-audio-fasttrack-dkms
	tcp-brutal-dkms
	tyton-dkms-git
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

for pkg in "${PKGS[@]}"; do
	yay -Sy --noconfirm "$pkg"
done
