#!/usr/bin/env bash
# /qompassai/dotfiles/.config/tpm2-tss/tpm2ssh.sh
# Qompass AI TPM2-TSS Gen Script
# Copyright (C) 2025 Qompass AI, All rights reserved
#####################################################
set -euo pipefail
CUSTOM_TAG="${1:-qompass}"
HOSTNAME="$(hostname)"
DATESTAMP="$(date +%Y%m%d)"
KEY_LABEL="${CUSTOM_TAG}_${HOSTNAME}_${DATESTAMP}"
KEY_PATH="HS/SRK/${KEY_LABEL}"
PKCS11_STORE="${XDG_DATA_HOME:-$HOME/.local/share}/tpm2-pkcs11"
TPM_SOCKET="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/swtpm/swtpm-sock"
USERPIN=$(pass show tpm2/userpin)
SOPIN=$(pass show tpm2/sopin)
export TPM2TOOLS_TCTI="swtpm:device=unixio,path=${TPM_SOCKET}"
export TPM2_PKCS11_STORE="${PKCS11_STORE}"
mkdir -p "$PKCS11_STORE"
if ! pgrep -f "swtpm.*${TPM_SOCKET}" >/dev/null; then
    echo "Starting swtpm instance..."
    mkdir -p "$(dirname "$TPM_SOCKET")" "$XDG_RUNTIME_DIR/swtpm/state"
    swtpm socket \
        --tpm2 \
        --ctrl type=unixio,path="$XDG_RUNTIME_DIR/swtpm/swtpm.ctrl" \
        --server type=unixio,path="$TPM_SOCKET" \
        --flags startup-clear \
        --tpmstate dir="$XDG_RUNTIME_DIR/swtpm/state" \
        --log level=1 \
        --daemon
    sleep 1
fi
if [ ! -f "$PKCS11_STORE/tokens.sqlite3" ]; then
    echo "Initializing PKCS11 store..."
    tpm2_ptool init --path "$PKCS11_STORE"
fi
if ! tpm2_ptool listtokens --path "$PKCS11_STORE" | grep -q "$KEY_LABEL"; then
    echo "Creating TPM2 PKCS#11 token..."
    tpm2_ptool addtoken --path "$PKCS11_STORE" \
        --pid=1 \
        --label="$KEY_LABEL" \
        --userpin="${USERPIN}" \
        --so="${SOPIN}"
fi
tpm2_createprimary -C o -g sha256 -G rsa -c primary.ctx
tpm2_create -G rsa -u key.pub -r key.priv -C primary.ctx
tpm2_load -C primary.ctx -u key.pub -r key.priv -c key.ctx
tpm2_evictcontrol -C o -c key.ctx 0x81010002
tpm2_readpublic -c 0x81010002 -f pem -o tpmkey.pem
ssh-keygen -i -m PKCS8 -f tpmkey.pem >~/.ssh/id_tpm.pub
