#!/bin/sh -x

# It will be run with two args: buildroot spec
BUILDROOT="$1"
SPEC="$2"

. $(dirname $0)/common.sh

# SteamCMD is 32-bit, needs i586 libraries
if [ "$(epm print info -s)" = "alt" ] ; then
    add_requires i586-glibc-core
fi
