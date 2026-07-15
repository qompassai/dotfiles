#!/bin/sh

PKGNAME=tixati
SUPPORTEDARCHES="x86_64"
VERSION="$2"
RELEASE="$3"
DESCRIPTION='It is a New and Powerful P2P System'
URL="https://tixati.com/"

. $(dirname $0)/common.sh

case "$(epm print info -p)" in
    rpm)
        mask="tixati-${VERSION}-${RELEASE}.x86_64.rpm"
        ;;
    *)
        mask="tixati_${VERSION}-${RELEASE}_amd64.deb"
        ;;
esac

if [ "$VERSION" = "*" ] ; then
    PKGURL="$(eget --list --latest "https://download.tixati.com/" "$mask")"
else
    PKGURL="https://download.tixati.com/$mask"
fi

install_pkgurl
