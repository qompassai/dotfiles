#!/bin/sh

PKGNAME=obs-studio-plugin-distroav
SUPPORTEDARCHES="x86_64"
VERSION="$2"
DESCRIPTION="DistroAV (OBS-NDI) - NDI integration for OBS Studio"
URL="https://github.com/DistroAV/DistroAV"

. $(dirname $0)/common.sh

# distroav-6.1.1-x86_64-linux-gnu.deb
PKGURL=$(get_github_url DistroAV/DistroAV "distroav-${VERSION}-x86_64-linux-gnu.deb")

install_pkgurl
