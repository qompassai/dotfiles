#!/bin/sh

PKGNAME=guitar
SUPPORTEDARCHES="x86_64"
VERSION="$2"
DESCRIPTION="Guitar - Git GUI client"
URL="https://github.com/soramimi/Guitar"

. $(dirname $0)/common.sh

if [ "$VERSION" = "*" ] ; then
    VERSION=$(get_github_tag "https://github.com/soramimi/Guitar/")
    [ -n "$VERSION" ] || fatal "Can't get version"
    VERSION=$(echo "$VERSION" | sed 's/^v//')
fi

PKGURL="https://github.com/soramimi/Guitar/releases/download/v$VERSION/guitar_${VERSION}_amd64.deb"

install_pkgurl
