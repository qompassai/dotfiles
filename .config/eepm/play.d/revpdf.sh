#!/bin/sh

PKGNAME=revpdf_editor
SUPPORTEDARCHES="x86_64 aarch64"
VERSION="$2"
DESCRIPTION=''
#DESCRIPTION="RevPDF - Privacy-First PDF Editor from the official site"
URL="https://revpdf.com/"

. $(dirname $0)/common.sh

warn_version_is_not_supported
export EPM_REPACK_VERSION="1.0"

arch="$(epm print info -a)"
PKGURL="https://github.com/Pawandeep-prog/revpdf-release/raw/refs/heads/main/linux/revpdf_editor-$arch.AppImage"

install_pkgurl
