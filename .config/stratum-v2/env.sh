#!/usr/bin/env bash
# /qompassai/dotfiles/.config/stratum-v2/env.sh
# Qompass AI Stratum-V2 Env Script
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
export STRATUM_V2_CONFIG="$HOME/.config/stratum-v2"
export TPROXY_CONFIG="$STRATUM_V2_CONFIG/tproxy-config.toml"
stratum-start() {
  cd ~/path/to/stratum
  cargo run --bin translator -- -c "$TPROXY_CONFIG"
}
stratum-logs() {
  tail -f ~/.config/stratum-v2/logs/*.log
}
