#!/bin/sh -x

# Generic repack script for any snap. Special script for target product will called after it.

# It will run with two args: buildroot spec
BUILDROOT="$1"
SPEC="$2"

PRODUCT="$(grep "^Name: " $SPEC | sed -e "s|Name: ||g" | head -n1)"
PRODUCTDIR=/opt/$PRODUCT

. $(dirname $0)/common.sh

cd .$PRODUCTDIR || fatal

# Workaround for plex
for i in usr/lib/x86_64-linux-gnu/libwebp* ; do
    move_file $PRODUCTDIR/$i $PRODUCTDIR/lib/$(basename $i)
done

for i in data-dir gnome-platform scripts lib/dri etc bin meta snap ; do
    remove_dir $PRODUCTDIR/$i
done

# Remove unnecessary files from usr/share
for i in usr/share/help usr/share/doc usr/share/locale usr/share/man usr/share/lintian ; do
    remove_dir $PRODUCTDIR/$i
done

# Check if app has binary in usr/bin
if [ -d usr/bin ] && ls usr/bin/* >/dev/null 2>&1 ; then
    # Create exec commands for all binaries found in desktop files
    main_bin=""
    for df in $BUILDROOT/usr/share/applications/*.desktop ; do
        [ -f "$df" ] || continue
        # Extract binary name from Exec=, removing quotes, path and arguments
        bin_name="$(grep -m1 '^Exec=' "$df" | sed -e 's|^Exec=||' -e 's|"||g' -e 's| .*||' -e 's|.*/||')"
        [ -n "$bin_name" ] && [ -f "usr/bin/$bin_name" ] || continue
        add_bin_exec_command $bin_name "$PRODUCTDIR/usr/bin/$bin_name"
        # Remember first binary as main
        [ -z "$main_bin" ] && main_bin="$bin_name"
    done
    # Create symlink from package name to main binary if different
    if [ -n "$main_bin" ] && [ "$main_bin" != "$PRODUCT" ] ; then
        add_bin_link_command $PRODUCT $main_bin
    elif [ -z "$main_bin" ] && [ -f "usr/bin/$PRODUCT" ] ; then
        add_bin_exec_command $PRODUCT "$PRODUCTDIR/usr/bin/$PRODUCT"
    fi
else
    remove_dir $PRODUCTDIR/usr
fi

for i in libEGL.so.1 libdrm.so.2 libdrm_amdgpu.so.1 libva-drm.so.2 libva-x11.so.2 libva.so.2 libcom_err.so.2 libdbus-1.so.3 libexpat.so.1 libkeyutils.so.1 ; do
    remove_file $PRODUCTDIR/lib/$i
done

for i in command.sh desktop-common.sh desktop-gnome-specific.sh desktop-init.sh ; do
    remove_file $PRODUCTDIR/$i
done

cd >/dev/null

# detect Chromium/Electron-based application
if [ -n "$(find "$BUILDROOT$PRODUCTDIR" -name 'v8_context_snapshot.bin' -print -quit 2>/dev/null)" ] ; then
    # Electron apps have resources/ dir, browsers don't
    if [ -d "$BUILDROOT$PRODUCTDIR/resources" ] ; then
        echo "Electron-based application detected, adding requires for it ..."
        add_electron_deps
    else
        fix_chrome_sandbox
    fi
fi
