#!/usr/bin/env bash

# gdb.sh
# Qompass AI - [ ]
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
xport -f process_file
process_file()
{
    local file="$1"
    # Only process ELF files with debug sections
    if readelf -S "$file" 2> /dev/null | grep -q debug_info; then
        gdb-add-index "$file" 2> /dev/null || true
    fi
}
export -f process_file
find /usr/bin /usr/lib -type f -executable -print0 2> /dev/null \
    | xargs -0 -P $(nproc) -I {} bash -c 'process_file "{}"'
exit 0
