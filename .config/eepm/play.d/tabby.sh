#!/bin/sh

PKGNAME=tabby
SUPPORTEDARCHES="x86_64"
VERSION="$2"
DESCRIPTION="Self-hosted AI coding assistant"
URL="https://github.com/TabbyML/tabby"

. $(dirname $0)/common.sh

if [ "$VERSION" = "*" ] ; then
    VERSION="$(get_github_tag TabbyML/tabby)"
fi

PKGURL="https://github.com/TabbyML/tabby/releases/download/v$VERSION/tabby_x86_64-manylinux_2_28.tar.gz"

install_pack_pkgurl
