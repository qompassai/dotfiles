#!/bin/sh

PKGNAME=steamcmd
SUPPORTEDARCHES="x86_64"
VERSION="$2"
DESCRIPTION="Steam console client for downloading game servers"
URL="https://developer.valvesoftware.com/wiki/SteamCMD"

. $(dirname $0)/common.sh

warn_version_is_not_supported

PKGURL="https://steamcdn-a.akamaihd.net/client/installer/steamcmd_linux.tar.gz"

install_pack_pkgurl

# install 32-bit support
epm prescription i586-support
