#!/bin/bash
# ~/sasl.sh
# ---------
# Copyright (C) 2025 Qompass AI, All rights reserved

SASL_FILE="$HOME/.config/postfix-psql/sasl_passwd"
SASL_DB="$SASL_FILE.lmdb"
> "$SASL_FILE"
echo "foamedmap@gmail.com [smtp.gmail.com]:587:foamedmap@gmail.com:$(pass show gmail/foamedmap/apppass)" >> "$SASL_FILE"
echo "map26@gmail.com [smtp.gmail.com]:587:map26@gmail.com:$(pass show gmail/map26/apppass)" >> "$SASL_FILE"

echo "map@qompass.ai [smtp.qompass.ai]:587:map@qompass.ai:$(pass show beacon/pass)" >> "$SASL_FILE"

postmap lmdb:"$SASL_FILE"

chmod 600 "$SASL_FILE" "$SASL_DB"
