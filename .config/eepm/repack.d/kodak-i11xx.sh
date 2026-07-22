#!/bin/sh

# It will be run with two args: buildroot spec
BUILDROOT="$1"
SPEC="$2"

. $(dirname $0)/common.sh

# Keep RPM sane drivers in /usr/lib64/sane.
if [ -d "$BUILDROOT/usr/lib/sane" ] ; then
    mkdir -p "$BUILDROOT/usr/lib64/sane"
    for f in "$BUILDROOT/usr/lib/sane/"* ; do
        [ -e "$f" ] || continue
        name="$(basename "$f")"
        move_file "/usr/lib/sane/$name" "/usr/lib64/sane/$name"
    done
    remove_dir /usr/lib/sane
fi
