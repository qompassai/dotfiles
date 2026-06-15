#!/bin/sh

PKGNAME=stirling-pdf
SUPPORTEDARCHES="x86_64 aarch64"
VERSION="$2"
DESCRIPTION="Web application for PDF operations (merge, split, convert, OCR)"
URL="https://github.com/Stirling-Tools/Stirling-PDF"

. $(dirname $0)/common.sh

if ! epm installed java-21-openjdk || ! epm installed java-21-openjdk-headless ; then
    info "Java 21 is required. Installing..."
    epm install java-21-openjdk-headless || fatal "Failed to install Java 21"
fi

if [ "$VERSION" = "*" ] ; then
    VERSION=$(get_github_tag "$URL")
    [ -n "$VERSION" ] || fatal "Can't get version from GitHub"
fi

PKGURL="$URL/releases/download/v$VERSION/Stirling-PDF-with-login.jar"

install_pack_pkgurl "$VERSION"
