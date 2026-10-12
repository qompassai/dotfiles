#!/usr/bin/env bash
# /qompassai/dotfiles/.config/bash/conf.d/options.sh
# Qompass AI Bash Options Config
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
# Shell options, set explicitly (previously none were set anywhere;
# history-related options live in history.sh). Options whose value
# is a deliberate choice rather than a default worth changing are
# set off explicitly so the decision is on the record.
shopt -s autocd
shopt -s cdspell
shopt -s checkhash
shopt -s checkwinsize
shopt -s direxpand
shopt -s dirspell
shopt -u dotglob
shopt -s extglob
shopt -s globstar
shopt -s hostcomplete
shopt -s nocaseglob
shopt -u nullglob
shopt -s progcomp
