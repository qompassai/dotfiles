#!/usr/bin/env bash
# /qompassai/dotfiles/.config/bash/conf.d/99_path.sh
# Qompass AI Bash Path Script
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
# PATH itself is owned by 00_xdg.sh (~/.local/bin, case-guarded) and
# by each language file (case-guarded prepends/appends), so nested
# shells no longer accumulate duplicates; the old dedupe-and-prepend
# dance that lived here is gone. What remains is the manual/info
# search path. Trailing colons keep the system defaults appended.
export INFOPATH="$HOME/.local/share/info:/usr/local/share/info:/usr/share/info:"
export MANPATH="$HOME/.local/share/man:/usr/local/share/man:/usr/share/man:"
if [ -d "$HOME/.opam/default/man" ]; then
    export MANPATH="$HOME/.opam/default/man:$MANPATH"
fi
