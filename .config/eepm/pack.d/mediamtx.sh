#!/bin/sh

TAR="$1"
RETURNTARNAME="$2"

. $(dirname $0)/common.sh

# mediamtx_v1.15.6_linux_amd64.tar.gz -> mediamtx-1.15.6.tar
VERSION="$(basename "$TAR" | sed -e 's|.*_v||' -e 's|_linux.*||')"
PKGNAME="$PRODUCT-$VERSION"

mkdir -p opt/$PRODUCT
tar xzf $TAR
mv mediamtx mediamtx.yml LICENSE opt/$PRODUCT/

erc pack $PKGNAME.tar opt

cat <<EOF >$PKGNAME.tar.eepm.yaml
name: $PRODUCT
version: $VERSION
group: Video
license: MIT
url: https://github.com/bluenviron/mediamtx
summary: Ready-to-use SRT / WebRTC / RTSP / RTMP / LL-HLS media server
description: MediaMTX is a ready-to-use and zero-dependency real-time media server and media proxy that allows to publish, read, proxy, record and playback video and audio streams.
EOF

return_tar $PKGNAME.tar
