#!/bin/sh

PKGNAME=wasistlos
SUPPORTEDARCHES="x86_64"
VERSION="$2"
DESCRIPTION="WhatsApp desktop application (from the repository or via wasistlos)"
URL="https://github.com/xeco23/WasIstLos"

. $(dirname $0)/common.sh

epm install $PKGNAME && exit 0

epm play wasistlos

