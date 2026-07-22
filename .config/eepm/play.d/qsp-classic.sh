#!/bin/sh

PKGNAME=QSP_Classic
SUPPORTEDARCHES="x86_64"
VERSION="$2"
RELEASE="$3"
DESCRIPTION='Classic QSP player'
URL="https://github.com/QSPFoundation/qspgui/releases"

. $(dirname $0)/common.sh

arch=x86_64
if [ "$VERSION" = "*" ] ; then
    PKGURL=$(get_github_url "https://github.com/QSPFoundation/qspgui/" "${PKGNAME}-${VERSION}-$arch.AppImage")
else
    # allow use 5.x.x-beta format
    [ -z "$CHECKED_VERSION" ] && [ "$RELEASE" != "*" ] && VERSION="$VERSION-$RELEASE"
    # replace ~ with - for URL (VERSION may contain ~b1 for pre-release)
    URLVERSION="$(echo "$VERSION" | tr '~' '-')"
    PKGURL="https://github.com/QSPFoundation/qspgui/releases/download/v$URLVERSION/${PKGNAME}-$URLVERSION-$arch.AppImage"
fi

install_pkgurl
