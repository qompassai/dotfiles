#!/bin/sh -x

# It will be run with two args: buildroot spec
BUILDROOT="$1"
SPEC="$2"

PRODUCTDIR=/opt/wasistlos

. $(dirname $0)/common.sh

# Remove bundled libwayland - use system ones
# Old bundled libwayland conflicts with system Mesa EGL
remove_file $PRODUCTDIR/usr/lib/x86_64-linux-gnu/libwayland-client.so.0
remove_file $PRODUCTDIR/usr/lib/x86_64-linux-gnu/libwayland-client.so.0.20.0
remove_file $PRODUCTDIR/usr/lib/x86_64-linux-gnu/libwayland-server.so.0
remove_file $PRODUCTDIR/usr/lib/x86_64-linux-gnu/libwayland-server.so.0.20.0
remove_file $PRODUCTDIR/usr/lib/x86_64-linux-gnu/libwayland-cursor.so.0
remove_file $PRODUCTDIR/usr/lib/x86_64-linux-gnu/libwayland-cursor.so.0.20.0
remove_file $PRODUCTDIR/usr/lib/x86_64-linux-gnu/libwayland-egl.so.1
remove_file $PRODUCTDIR/usr/lib/x86_64-linux-gnu/libwayland-egl.so.1.20.0

# Fix hardcoded webkit paths in libwebkit2gtk
# WebKit uses posix_spawn which bypasses AppRun hooks, so we need to patch the binary
# See: https://github.com/AppImageCrafters/appimage-builder/issues/175
WEBKIT_LIB="$BUILDROOT$PRODUCTDIR/usr/lib/x86_64-linux-gnu/libwebkit2gtk-4.1.so.0.1.4"
if [ -f "$WEBKIT_LIB" ] ; then
    # Create symlink to actual webkit directory
    ln -s usr/lib/x86_64-linux-gnu/webkit2gtk-4.1 "$BUILDROOT$PRODUCTDIR/webkit2gtk-4.1"
    pack_file $PRODUCTDIR/webkit2gtk-4.1
    # Create symlink for injected bundle (webkit looks in base dir, not injected-bundle subdir)
    ln -s injected-bundle/libwebkit2gtkinjectedbundle.so "$BUILDROOT$PRODUCTDIR/usr/lib/x86_64-linux-gnu/webkit2gtk-4.1/libwebkit2gtkinjectedbundle.so"
    pack_file $PRODUCTDIR/usr/lib/x86_64-linux-gnu/webkit2gtk-4.1/libwebkit2gtkinjectedbundle.so
    # Patch hardcoded path
    # /usr/lib/x86_64-linux-gnu/webkit2gtk-4.1 (40 chars) -> /opt/wasistlos/webkit2gtk-4.1 (30 chars)
    patch_binary "$WEBKIT_LIB" "/usr/lib/x86_64-linux-gnu/webkit2gtk-4.1" "/opt/wasistlos/webkit2gtk-4.1"
fi

# Set GIO_MODULE_DIR for TLS support (GnuTLS module for HTTPS)
echo 'GIO_MODULE_DIR=$APPDIR/usr/lib/x86_64-linux-gnu/gio/modules' >> "$BUILDROOT$PRODUCTDIR/.env"
