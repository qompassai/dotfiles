#!/bin/sh

PKGNAME=Gittyup
SUPPORTEDARCHES="x86_64"
VERSION="$2"
DESCRIPTION="Gittyup - graphical Git client (GitAhead fork)"
URL="https://github.com/Murmele/Gittyup"

. $(dirname $0)/common.sh

if [ "$VERSION" = "*" ] ; then
    VERSION=$(get_github_tag "https://github.com/Murmele/Gittyup/")
    [ -n "$VERSION" ] || fatal "Can't get version"
    # Remove gittyup_v prefix
    VERSION=$(echo "$VERSION" | sed 's/^gittyup_v//')
fi

PKGURL="https://github.com/Murmele/Gittyup/releases/download/gittyup_v$VERSION/Gittyup-$VERSION-x86_64.AppImage"

install_pkgurl
