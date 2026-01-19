#!/usr/bin/env bash
# /qompassai/dotfiles/.config/vault/vault.sh
# Qompass AI Vault Wrapper Script
# Copyright (C) 2025 Qompass AI, All rights reserved
#################################################
CONSUL_ADDRESS="$(pass show vault/consul-address)"
KMS_KEY_ID="$(pass show vault/kms-key-id)"
PKCS11_PIN="$(pass show vault/pkcs11-pin)"
envsubst < "$XDG_CONFIG_HOME/vault/vault.hcl.tmpl" | \
  sed "s|{{CONSUL_ADDRESS}}|$CONSUL_ADDRESS|g" | \
  sed "s|{{KMS_KEY_ID}}|$KMS_KEY_ID|g" | \
  sed "s|{{PKCS11_PIN}}|$PKCS11_PIN|g" \
  > "$XDG_CONFIG_HOME/vault/vault.hcl"
vault server -config="$XDG_CONFIG_HOME/vault/vault.hcl"
