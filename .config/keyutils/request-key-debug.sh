#!/bin/sh
# /qompassai/dotfiles/.config/keyutils/request-key-debug.sh
# Qompass AI KeyUtils Config
# Copyright (C) 2025 Qompass AI, All rights reserved
#########################################################################
# Call: request-key-debug.sh <keyid> <desc> <callout> <session-keyring>
#

echo RQDebug keyid: $1
echo RQDebug desc: $2
echo RQDebug callout: $3
echo RQDebug session keyring: $4

if [ "$3" != "neg" ]
then
    keyctl instantiate $1 "Debug $3" $4 || exit 1
else
    cat /proc/keys
    echo keyctl negate $1 30 $4
    keyctl negate $1 30 $4
fi

exit 0
