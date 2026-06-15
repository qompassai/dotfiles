#!/bin/sh

PKGNAME=kodak-i2000
SUPPORTEDARCHES="x86_64"
VERSION="$2"
DESCRIPTION="Kodak Alaris i2000 series scanner driver (i2620)"
URL="https://www.kodakalaris.com/en/scanners/i2620-scanner"

. $(dirname $0)/common.sh

warn_version_is_not_supported

PKGURL="https://resources.kodakalaris.com/docimaging/drivers/LinuxSoftware_i2000_v4.14.x86_64.deb.tar.gz"

install_pack_pkgurl
