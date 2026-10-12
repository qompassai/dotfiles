#!/usr/bin/env bash
# /qompassai/dotfiles/.config/bash/conf.d/starknet.sh
# Qompass AI Bash Starknet Config
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
# The completion registrations pointed at _snforge/_sncast, which
# are defined by the starknet-foundry completion scripts; with the
# tools absent, pressing Tab on snforge/sncast errored. They now
# register only when the functions actually exist.
if type _snforge > /dev/null 2>&1; then
    complete -o default -F _snforge snforge
fi
if type _sncast > /dev/null 2>&1; then
    complete -o default -F _sncast sncast
fi
