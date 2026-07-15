#!/bin/sh

PKGNAME=ipfs-desktop
SUPPORTEDARCHES="x86_64"
VERSION="$2"
DESCRIPTION="IPFS Desktop - desktop client for the InterPlanetary File System from the official site"
URL="https://github.com/ipfs/ipfs-desktop"

. $(dirname $0)/common.sh

# https://github.com/ipfs/ipfs-desktop/releases/download/v0.47.0/ipfs-desktop-0.47.0-linux-amd64.deb
if [ "$VERSION" = "*" ] ; then
    PKGURL=$(get_github_url "$URL" "ipfs-desktop-${VERSION}-linux-amd64.deb")
else
    PKGURL="https://github.com/ipfs/ipfs-desktop/releases/download/v$VERSION/ipfs-desktop-$VERSION-linux-amd64.deb"
fi

install_pkgurl
