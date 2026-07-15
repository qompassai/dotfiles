#!/bin/sh

PKGNAME=teamspeak3-server
SUPPORTEDARCHES="x86_64"
VERSION="$2"
DESCRIPTION="TeamSpeak3 Server for Linux from the official site"
URL="https://www.teamspeak.com/"

. $(dirname $0)/common.sh

if [ "$VERSION" = "*" ] ; then
    PKGURL=$(eget --list --latest https://teamspeak.com/en/downloads/ "teamspeak3-server_linux_amd64-*.tar.bz2")
else
    PKGURL="https://files.teamspeak-services.com/releases/server/${VERSION}/teamspeak3-server_linux_amd64-${VERSION}.tar.bz2"
fi

install_pack_pkgurl || exit

cat <<EOF
Run to start TeamSpeak3 Server:
# serv teamspeak3-server on
or
# systemctl enable --now teamspeak3-server
EOF
