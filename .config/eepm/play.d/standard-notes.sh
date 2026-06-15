#!/bin/sh

PKGNAME=standard-notes
SUPPORTEDARCHES="x86_64"
VERSION="$2"
DESCRIPTION='Standard Notes - encrypted notes app from the official site'
URL="https://standardnotes.com"

. $(dirname $0)/common.sh

arch=amd64
pkgtype=deb

PKGURL=$(eget --list --latest https://github.com/standardnotes/app/releases/ "$PKGNAME*$VERSION*linux-$arch.$pkgtype")

install_pkgurl
