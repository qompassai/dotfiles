#!/bin/sh

PKGNAME=dorion
SUPPORTEDARCHES="x86_64 aarch64 armhf"
VERSION="$2"
RELEASE="$3"
DESCRIPTION="Dorion - lightweight alternative Discord client"
URL="https://github.com/SpikeHD/Dorion"

. $(dirname $0)/common.sh

arch="$(epm print info -a)"
pkgtype="$(epm print info -p)"

case "$pkgtype" in
    rpm)
        # Dorion_6.11.0-1.x86_64.rpm / Dorion_6.11.0-1.aarch64.rpm / Dorion_6.11.0-1.armhfp.rpm
        [ "$arch" = "armhf" ] && arch="armhfp"
        PKGURL="$(get_github_url SpikeHD/Dorion Dorion_${VERSION}-${RELEASE}.${arch}.rpm)"
        ;;
    *)
        # Dorion_6.11.0_amd64.deb / Dorion_6.11.0_arm64.deb / Dorion_6.11.0_armhf.deb
        arch="$(epm print info --distro-arch)"
        [ "$arch" = "armv7l" ] && arch="armhf"
        PKGURL="$(get_github_url SpikeHD/Dorion Dorion_${VERSION}_${arch}.deb)"
        ;;
esac

install_pkgurl
