#!/bin/sh

PKGNAME=linkmeter-cli
SUPPORTEDARCHES="x86_64 aarch64"
VERSION="$2"
DESCRIPTION="Linkmeter CLI - network speed testing tool"
URL="https://linkmeter.net/"

. $(dirname $0)/common.sh

warn_version_is_not_supported

# Download real binary directly (official packages contain only a downloader script)
arch=$(epm print info -a)
PKGURL="https://api.linkmeter.net/linkmeter-cli_$arch"

install_pack_pkgurl
