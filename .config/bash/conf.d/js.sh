# js.sh
# Qompass AI - [ ]
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
: "${PNPM_HOME:=$HOME/.local/share/pnpm}"
if [ -d "$PNPM_HOME" ]; then
    case ":$PATH:" in
        *":$PNPM_HOME:"*) : ;;
        *) PATH="$PNPM_HOME:$PATH" ;;
    esac
    export PNPM_HOME PATH
fi
