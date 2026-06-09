#!/usr/bin/env bash

# framemagick.sh
# Qompass AI - [ ]
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
set -euo pipefail
IMCONF_ROOT="${XDG_CONFIG_HOME:-$HOME/.config}/ImageMagick/subliminal"
source "${IMCONF_ROOT}/imagick_subliminal.env"

OUTDIR="${OUTDIR:-annotated}"
mkdir -p "$OUTDIR"

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 frame1.png [frame2.png ...]"
    exit 1
fi

for frame in "$@"; do
    base="$(basename "$frame")"
    out="$OUTDIR/$base"
    magick "$frame" \
        -font "$IM_FONT" \
        -gravity "$IM_GRAVITY" \
        -pointsize "$IM_POINTSIZE" \
        -stroke "$IM_STROKE" -strokewidth "$IM_STROKEWIDTH" \
        -fill "rgba(255,255,255,$IM_OPACITY)" \
        -annotate "$IM_OFFSET" "$IM_TEXT" \
        "$out"
    echo "Annotated $frame -> $out"
done
