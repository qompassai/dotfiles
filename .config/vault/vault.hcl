# /qompassai/dotfiles/.config/vault/vault.hcl
# Qompass AI Vault Config
# Copyright (C) 2025 Qompass AI, All rights reserved
#################################################
ui = true
mlock = true
disable_mlock = true

storage "file" {
  path = "${XDG_DATA_HOME}/vault"
}

storage "consul" {
  address = "{{CONSUL_ADDRESS}}"
  path    = "vault"
}

listener "tcp" {
  address = "127.0.0.1:8200"
  tls_disable = 1
}

listener "tcp" {
  address       = "0.0.0.0:8200"
  tls_cert_file = "${XDG_CONFIG_HOME}/vault/tls/tls.crt"
  tls_key_file  = "${XDG_CONFIG_HOME}/vault/tls/tls.key"
}

license_path = "${XDG_CONFIG_HOME}/vault/license/vault.hclic"

seal "awskms" {
  region = "us-east-1"
  kms_key_id = "{{KMS_KEY_ID}}"
}

seal "pkcs11" {
  lib            = "${XDG_DATA_HOME}/vault/lib/libCryptoki2_64.so"
  slot           = "0"
  pin            = "{{PKCS11_PIN}}"
  key_label      = "vault-hsm-key"
  hmac_key_label = "vault-hsm-hmac-key"
}

