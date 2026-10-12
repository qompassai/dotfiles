#!/usr/bin/env bash
# /qompassai/dotfiles/.config/bash/conf.d/ocaml.sh
# Qompass AI Bash Ocaml Config
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
# The opam init was commented out while ~/.opam exists and 99_path
# already points MANPATH at the default switch; enabled again.
# opam's init prepends its bin directory unguarded, so it is only
# sourced when that directory is not already on PATH (keeps nested
# and re-sourced shells duplicate-free).
case ":$PATH:" in
    *":$HOME/.opam/default/bin:"*) ;;
    *)
        if [ -r "${HOME}/.opam/opam-init/init.sh" ]; then
            # shellcheck disable=SC1091
            . "${HOME}/.opam/opam-init/init.sh" > /dev/null 2>&1 || true
        fi
        ;;
esac
