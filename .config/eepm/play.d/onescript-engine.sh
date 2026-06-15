#!/bin/sh

PKGNAME=onescript-engine
SUPPORTEDARCHES="x86_64"
VERSION="$2"
RELEASE="$3"
DESCRIPTION="OneScript Engine from the official site"
TIPS="Run epm play onescript-engine=<version> to install specific version (e.g. 2.0.0 or 1.9.3)."
URL="https://github.com/EvilBeaver/OneScript"

. $(dirname $0)/common.sh

if [ "$VERSION" = "*" ] ; then
    VERSION=$(get_github_tag "https://github.com/EvilBeaver/OneScript/")
fi

# linux-x64.zip (self-contained) appeared in 2.0.0
# for older versions use deb/rpm from GitHub
if [ "$(epm print compare "$VERSION" 2.0.0)" != "-1" ] ; then
    PKGURL="https://github.com/EvilBeaver/OneScript/releases/download/v$VERSION/OneScript-$VERSION-linux-x64.zip"
    install_pack_pkgurl
else
    pkgtype=$(epm print info -p)
    case $pkgtype in
        rpm)
            PKGURL="https://github.com/EvilBeaver/OneScript/releases/download/v${VERSION}/onescript-engine-${VERSION}-${RELEASE}.fc26.noarch.rpm"
            ;;
        *)
            PKGURL="https://github.com/EvilBeaver/OneScript/releases/download/v$VERSION/onescript-engine_${VERSION}_all.deb"
            ;;
    esac
    install_pkgurl
fi
