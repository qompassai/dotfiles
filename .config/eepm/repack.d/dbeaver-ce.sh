#!/bin/sh -x
# It will run with two args: buildroot spec
BUILDROOT="$1"
SPEC="$2"

PRODUCTCUR=dbeaver

. $(dirname $0)/common.sh

# Remove JNA libraries for non-Linux platforms (they create false dependencies like libc.so.1/7/8)
for i in aix darwin dragonflybsd freebsd openbsd sunos win32 ; do
    for dir in $BUILDROOT/usr/share/dbeaver-ce/plugins/com.sun.jna_*/com/sun/jna/$i* ; do
        [ -d "$dir" ] && remove_dir "${dir#$BUILDROOT}"
    done
done

move_to_opt
rm usr/bin/$PRODUCT
add_bin_link_command $PRODUCT $PRODUCTDIR/$PRODUCTCUR
add_bin_link_command $PRODUCTCUR $PRODUCT

fix_desktop_file "/usr/share/dbeaver-ce/dbeaver"
fix_desktop_file "/usr/share/dbeaver-ce/dbeaver.png"
fix_desktop_file "/usr/share/dbeaver-ce/" "$PRODUCTDIR/"

install_file .$PRODUCTDIR/dbeaver.png /usr/share/pixmaps/dbeaver.png
