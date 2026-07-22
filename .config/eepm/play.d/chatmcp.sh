#!/bin/sh

PKGNAME=chatmcp
SUPPORTEDARCHES="x86_64"
VERSION="$2"
DESCRIPTION="ChatMCP - AI chat client with MCP support"
URL="https://github.com/daodao97/chatmcp"

. $(dirname $0)/common.sh

pkgtype="$(epm print info -p)"

if ! is_glibc_enough 2.34 ; then
    fatal "Версия glibc слишком старая, требуется система с glibc 2.34 и выше."
fi


case "$pkgtype" in
    rpm)
        # chatmcp-0.0.76-linux.rpm
        PKGURL="$(get_github_url daodao97/chatmcp $PKGNAME-${VERSION}-linux.rpm)"
        ;;
    *)
        # chatmcp-0.0.76-linux.deb
        PKGURL="$(get_github_url daodao97/chatmcp $PKGNAME-${VERSION}-linux.deb)"
        ;;
esac

install_pkgurl
