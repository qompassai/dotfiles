#!/bin/sh -x

BUILDROOT="$1"
SPEC="$2"

PRODUCT=Dorion

. $(dirname $0)/common.sh

# Dorion is a Tauri application (Rust + WebView)
# License is GPL-3.0 per https://github.com/SpikeHD/Dorion

# Fix empty License field from original package
subst "s|^License:.*|License: GPL-3.0|" $SPEC

# Move lib files to /opt/Dorion
move_to_opt /usr/lib/$PRODUCT

# Move binary from /usr/bin to /opt/Dorion
move_file /usr/bin/$PRODUCT $PRODUCTDIR/$PRODUCT

add_bin_link_command $PRODUCT
add_bin_link_command dorion $PRODUCT
