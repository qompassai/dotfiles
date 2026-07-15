#!/bin/sh

PKGNAME=meridius
SUPPORTEDARCHES="x86_64"
VERSION="$2"
DESCRIPTION="Meridius — music player for VK"
URL="https://github.com/PurpleHorrorRus/Meridius"

. $(dirname $0)/common.sh

if [ "$VERSION" = "*" ] ; then
    PKGURL=$(get_github_url "$URL" "$PKGNAME-*.tar.gz")
else
    PKGURL="https://github.com/PurpleHorrorRus/Meridius/releases/download/v$VERSION/meridius-$VERSION.tar.gz"
fi

install_pack_pkgurl
