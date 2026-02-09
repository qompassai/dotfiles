#!/usr/bin/env bash

# nv.sh
# Qompass AI - [ ]
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
set -euo pipefail
PYTHON_SCRIPT="$XDG_CONFIG_HOME/pacman/scripts/nvp.py"
LOG_DIR="/var/log/nvidia-patch"
BACKUP_DIR="/var/lib/nvidia-patch/backups"
mkdir -p "${LOG_DIR}" "${BACKUP_DIR}"
log()
{
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${LOG_DIR}/patch.log"
}
log "==> Starting NVIDIA patch process"
while IFS= read -r target; do
    if [[ -f ${target} ]]; then
        log "Processing: ${target}"
        backup_file="${BACKUP_DIR}/$(basename "${target}").$(date +%s).bak"
        cp "${target}" "${backup_file}"
        log "Backup created: ${backup_file}"
        if echo "y" | python -B "${PYTHON_SCRIPT}" "${target}" >> "${LOG_DIR}/patch.log" 2>&1; then
            log "Successfully patched: ${target}"
        else
            log "ERROR: Failed to patch ${target}"
            cp "${backup_file}" "${target}"
            log "Restored from backup"
        fi
    else
        log "WARNING: Target not found: ${target}"
    fi
done
log "==> NVIDIA patch process completed"
