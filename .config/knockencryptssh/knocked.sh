#!/bin/bash
# /qompassai/dotfiles/.config/knockerencryptssh/knocked.sh
# Qompass AI KnockerEncryptssh Knocked Script
# Copyright (C) 2025 Qompass AI, All rights reserved
#################################################
serve

KES_TEMPDIR="/tmp/knockencryptssh_initrd"


if [ "${1}" == "keyfile" -o "${1}" == "passphrase" ]
then
    ([ -d "${KES_TEMPDIR}" ] || mkdir -p "${KES_TEMPDIR}" ) && touch "${KES_TEMPDIR}/knockencryptssh.${1}"
fi
