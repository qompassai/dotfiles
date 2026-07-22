#!/bin/sh

PKGNAME=thincast-client
SUPPORTEDARCHES="x86_64 aarch64"
VERSION="$2"
DESCRIPTION="Thincast Remote Desktop Client (RDP) from the snapcraft"
URL="https://snapcraft.io/thincast-client"

. $(dirname $0)/common.sh

warn_version_is_not_supported

PKGURL="$(snap_get_pkgurl $URL)"
install_pkgurl
