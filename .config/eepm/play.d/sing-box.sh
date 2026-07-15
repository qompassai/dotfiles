#!/bin/sh

PKGNAME=sing-box
SUPPORTEDARCHES="x86_64 aarch64 armhf"
VERSION="$2"
DESCRIPTION="The universal proxy platform (sing-box)"
URL="https://github.com/SagerNet/sing-box"

. $(dirname $0)/common.sh

arch="$(epm print info --debian-arch)"

if [ "$VERSION" = "*" ] ; then
    PKGURL=$(get_github_url "https://github.com/SagerNet/sing-box/" "sing-box_${VERSION}_linux_$arch.deb")
else
    PKGURL="https://github.com/SagerNet/sing-box/releases/download/v$VERSION/sing-box_${VERSION}_linux_$arch.deb"
fi

install_pkgurl
