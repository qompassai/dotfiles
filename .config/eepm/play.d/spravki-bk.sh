#!/bin/sh

PKGNAME=spravki-bk
SUPPORTEDARCHES="x86_64"
VERSION="$2"
DESCRIPTION="Система подготовки отчетности «Справки БК»"
URL="http://www.kremlin.ru/structure/additional/12/"

. $(dirname $0)/common.sh

warn_version_is_not_supported

# WARNING: kremlin.ru does not support HTTPS, checksum verification is critical
# Get download URL for Astra Linux version from kremlin.ru
PKGURL=$(eget -q -O- http://www.kremlin.ru/structure/additional/12/ | grep -B1 "для Astra Linux" | grep -o 'href="[^"]*"' | sed 's/href="//;s/"//' | head -n 2 | tail -n 1)

# Checksum for version 3.0.4 (2025-04-01) - update when new version is released
PKGSUM="sha256:241fe546e22360b003bdc922f1e40d12bd1b87a01ce256d8b1739419718b6475"

install_pack_pkgurl "" "$PKGSUM"
