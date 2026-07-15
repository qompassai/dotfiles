#!/bin/sh

TAR="$1"
RETURNTARNAME="$2"

. $(dirname $0)/common.sh

mkdir -p opt/$PRODUCT
cp "$TAR" opt/$PRODUCT/$PRODUCT
chmod 755 opt/$PRODUCT/$PRODUCT

VERSION=$(opt/$PRODUCT/$PRODUCT --help 2>&1 | grep -oP 'Version: linkmeter-cli \K[0-9.]+')
[ -n "$VERSION" ] || VERSION="1.0"

PKGNAME=$PRODUCT-$VERSION

mkdir -p usr/bin
ln -s /opt/$PRODUCT/$PRODUCT usr/bin/$PRODUCT

cat <<EOF >$PKGNAME.tar.eepm.yaml
name: $PRODUCT
group: Networking/Other
license: Proprietary
url: https://linkmeter.net/
summary: Linkmeter CLI - network speed testing tool
description: Official linkmeter.net command line utility for testing internet connection speed and performance.
EOF

erc pack $PKGNAME.tar opt usr || fatal

return_tar $PKGNAME.tar
