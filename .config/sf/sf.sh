#!/usr/bin/env bash

# sf.sh
# Qompass AI Salesforce CLI Setup
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
sf config set --global disable-telemetry=true
sf config set --global org-api-version=63.0
sf config set --global org-capitalize-record-types=false
sf config set --global org-max-query-limit=20000
sf config set --global rest-deploy=false
sf config set --global target-dev-hub=your-devhub-alias
sf config set --global target-org=your-default-org-alias
