#!/usr/bin/env bash
# sf.sh
# Qompass AI Salesforce CLI Setup
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
set -euo pipefail
INSTANCE_URL="https://tdstelecom.my.salesforce.com"
DEFAULT_ORG_ALIAS="tds"
sf config set disable-telemetry=true --global
sf config set org-api-version=67.0 --global
sf config set org-capitalize-record-types=false --global
sf config set org-max-query-limit=20000 --global
sf config set rest-deploy=false --global
sf config set org-instance-url="${INSTANCE_URL}" --global
read -r -p "Enter Dev Hub alias (example: map-dev): " DEVHUB_ALIAS
if [[ -z ${DEVHUB_ALIAS} ]]; then
    echo "Error: Dev Hub alias cannot be empty."
    exit 1
fi
BROWSER=chrome sf org login web \
    --instance-url "${INSTANCE_URL}" \
    --alias "${DEVHUB_ALIAS}" \
    --set-default-dev-hub
sf config set target-dev-hub="${DEVHUB_ALIAS}" --global
sf config set target-org="${DEVHUB_ALIAS}" --global
echo "Dev Hub authorized and set."
echo "Default Dev Hub alias: ${DEVHUB_ALIAS}"
echo "Default org alias: ${DEVHUB_ALIAS}"
echo
echo "If you also want a general TDS alias, run:"
echo "  sf alias set ${DEFAULT_ORG_ALIAS}=\$(sf org display --target-org ${DEVHUB_ALIAS} --json | jq -r '.result.username')"
