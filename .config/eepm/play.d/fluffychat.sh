#!/bin/sh

PKGNAME=fluffychat
SUPPORTEDARCHES="x86_64 aarch64"
VERSION="$2"
DESCRIPTION="FluffyChat - open source, nonprofit and cute Matrix messenger from the official site"
URL="https://github.com/krille-chan/fluffychat"

. $(dirname $0)/common.sh

arch="$(epm print info -a)"
case "$arch" in
    x86_64)
        arch=x64
        ;;
    aarch64)
        arch=arm64
        ;;
    *)
        fatal "$arch arch is not supported"
        ;;
esac

# https://github.com/krille-chan/fluffychat/releases/download/v2.4.1/fluffychat-linux-x64.tar.gz
# https://github.com/krille-chan/fluffychat/releases/download/v2.4.1/fluffychat-linux-arm64.tar.gz
if [ "$VERSION" = "*" ] ; then
    PKGURL=$(get_github_url "$URL" "fluffychat-linux-$arch.tar.gz")
else
    PKGURL="https://github.com/krille-chan/fluffychat/releases/download/v$VERSION/fluffychat-linux-$arch.tar.gz"
fi

install_pack_pkgurl
