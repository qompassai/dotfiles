#!/usr/bin/env bash
# /qompassai/dotfiles/.config/unbound/clearnet.sh
# Unbound Clearnet Script
# Copyright (C) 2025 Qompass AI, All rights reserved
##############################################
curl -s --max-time 5 http://connectivity-check.ubuntu.com/ | grep -q "success" || {
    echo "Captive portal detected, switching to fallback DNS"
}
