#!/usr/bin/env bash
# /qompassai/dotfiles/.config/dkms/kernel.sh
# Qompass AI Linux DKMS Module Param Script
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
KVER="$(uname -r)"
MODULES_DIR="/usr/lib/modules/${KVER}"
OUT_PARAMS="modprobed.txt"
OUT_LOAD="modules_load_d.txt"
find "$MODULES_DIR" -type f -name '*.ko*' -printf '%f\n' \
  | sed 's/\.ko.*$//' \
  | sort -u > "$OUT_LOAD"
: > "$OUT_PARAMS"
while read -r m; do
  if modinfo -p "$m" > /dev/null 2>&1; then
    params="$(modinfo -p "$m")"
    if [ -n "$params" ]; then
      {
        echo "=== $m ==="
        echo "$params"
        echo
      } >> "$OUT_PARAMS"
    fi
  fi
done < "$OUT_LOAD"
