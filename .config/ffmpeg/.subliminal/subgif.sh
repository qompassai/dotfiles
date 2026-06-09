#!/usr/bin/env bash

# subgif.sh
# Qompass AI FFMPeg Subliminal Gif
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
set -euo pipefail
FFCONF_ROOT="${XDG_CONFIG_HOME:-$HOME/.config}/ffmpeg/subliminal"
source "$FFCONF_ROOT/ffmpeg_subliminal.env"
IN="${1:?input video or gif required}"
OUT="${2:-subliminal.gif}"
WORKDIR="${WORKDIR:-/tmp/subliminal_work}"
mkdir -p "$WORKDIR"
PALETTE="$WORKDIR/palette.png"
FILTER_TEMPLATE="$FFCONF_ROOT/ffmpeg_subliminal_text.ffscript"
FILTER_FILE="$WORKDIR/subliminal_filter.ffscript"
FONTFILE="$(fc-match -f '%{file}\n' "$FF_FONT")"
sed \
    -e "s|@@TEXT@@|$SUBLIMINAL_TEXT|g" \
    -e "s|@@FONTFILE@@|$FONTFILE|g" \
    -e "s|@FONTCOLOR@|$FF_FONTCOLOR|g" \
    -e "s|@FONTSIZE@|$FF_FONTSIZE|g" \
    -e "s|@X_EXPR@|$FF_X_EXPR|g" \
    -e "s|@Y_EXPR@|$FF_Y_EXPR|g" \
    -e "s|@T_START@|$FF_T_START|g" \
    -e "s|@T_END@|$FF_T_END|g" \
    "$FILTER_TEMPLATE" > "$FILTER_FILE"
ffmpeg -y -i "$IN" \
    -vf "fps=$FF_FPS,scale=480:-1:flags=lanczos,palettegen=max_colors=$FF_PALETTE_SIZE" \
    "$PALETTE"
ffmpeg -y -i "$IN" -i "$PALETTE" \
    -filter_complex_script "$FILTER_FILE" \
    -map "[v]" -map 1:v \
    -lavfi "fps=$FF_FPS,scale=480:-1:flags=lanczos[x];[x][1:v]paletteuse" \
    "$OUT"
echo "Done: $OUT"
