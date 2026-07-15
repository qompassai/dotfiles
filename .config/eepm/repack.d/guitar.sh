#!/bin/sh -x

# It will be run with two args: buildroot spec
BUILDROOT="$1"
SPEC="$2"

. $(dirname $0)/common.sh

# Qt6 dependencies (system Qt, not bundled)
add_unirequires libQt6Core.so.6 libQt6Gui.so.6 libQt6Svg.so.6 libQt6Widgets.so.6

install_file /usr/share/icons/guitar/Guitar.svg /usr/share/icons/hicolor/scalable/apps/Guitar.svg
remove_dir /usr/share/icons/guitar
fix_desktop_file /usr/bin/Guitar Guitar
fix_desktop_file /usr/share/icons/guitar/Guitar.svg Guitar
add_bin_link_command guitar /usr/bin/Guitar
