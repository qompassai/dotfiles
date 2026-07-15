#!/bin/sh

# It will be run with two args: buildroot spec
BUILDROOT="$1"
SPEC="$2"

. $(dirname $0)/common.sh

# remove JavaFX avcodec plugins that require old ffmpeg (libavcodec.so.52/53)
# media playback may not work without them
remove_file /opt/trainchineseDesktop/runtime/jre/lib/i386/fxavcodecplugin-*.so
