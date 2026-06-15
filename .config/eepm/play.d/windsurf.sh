#!/bin/sh

PKGNAME=windsurf
SUPPORTEDARCHES="x86_64"
VERSION="$2"
DESCRIPTION="Windsurf — AI-powered code editor by Codeium"
URL="https://windsurf.com"

. $(dirname $0)/common.sh

RELEASES_URL="https://windsurf.com/editor/releases"

if [ "$VERSION" = "*" ] ; then
    PKGURL=$(fetch_url "$RELEASES_URL" | grep -oP 'https://windsurf-stable\.codeiumdata\.com/linux-x64-deb/stable/[^"]+\.deb' | head -1)
else
    PKGURL=$(fetch_url "$RELEASES_URL" | grep -oP "https://windsurf-stable\.codeiumdata\.com/linux-x64-deb/stable/[^/]+/Windsurf-linux-x64-$VERSION\.deb" | head -1)
fi

install_pkgurl
