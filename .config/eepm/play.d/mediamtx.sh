#!/bin/sh

PKGNAME=mediamtx
SUPPORTEDARCHES="x86_64 aarch64"
VERSION="$2"
DESCRIPTION="Ready-to-use SRT / WebRTC / RTSP / RTMP / LL-HLS media server and media proxy"
URL="https://github.com/bluenviron/mediamtx"

. $(dirname $0)/common.sh

arch="$(epm print info -a)"
case "$arch" in
    x86_64)
        arch=amd64
        ;;
    aarch64)
        arch=arm64
        ;;
esac

if [ "$VERSION" = "*" ] ; then
    VERSION="$(get_github_tag "$URL/")"
fi

PKGURL="$URL/releases/download/v$VERSION/${PKGNAME}_v${VERSION}_linux_${arch}.tar.gz"

install_pack_pkgurl
