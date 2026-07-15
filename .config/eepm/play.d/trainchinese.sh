#!/bin/sh

PKGNAME=trainchineseDesktop
SUPPORTEDARCHES="i586 i686 x86_64"
VERSION="$2"
DESCRIPTION="TrainChinese - Chinese learning application from the official site"
URL="https://www.trainchinese.com/v2/viewApps.php?tcLanguage=ru#PC"

. $(dirname $0)/common.sh

warn_version_is_not_supported

PKGURL="https://www.trainchinese.com/desktop/download.php?type=linux"

# Site requires browser User-Agent
export EGET_OPTIONS="-U"

install_pkgurl
