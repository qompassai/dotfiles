#!/usr/bin/env bash
# /qompassai/Shell/.profile.d/17-qpg.sh
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
# Liboqs
export C_INCLUDE_PATH="/opt/qai/liboqs/include${C_INCLUDE_PATH:+:$C_INCLUDE_PATH}"
export LIBRARY_PATH="/opt/qai/liboqs/lib${LIBRARY_PATH:+:$LIBRARY_PATH}"
export LD_LIBRARY_PATH="/opt/qai/liboqs/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export LIBOQS_INCLUDE_DIR="/opt/qai/liboqs/include/oqs"
export LIBOQS_LIB_DIR="/opt/qai/liboqs/lib"
export PKG_CONFIG_PATH="/opt/qai/liboqs/lib/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
# GPG
export SSH_AUTH_SOCK=$(gpgconf --list-dirs agent-ssh-socket)
if [ "${gnupg_SSH_AUTH_SOCK_by:-0}" -ne $$ ]; then
  export SSH_AUTH_SOCK="$(gpgconf --list-dirs agent-ssh-socket)"
fi
export SSLKEYLOGFILE=/tmp/sslkeylog.log
export GPG_TTY=$(tty)
# Pass
export PASSWORD_STORE_DIR="$HOME/.password-store"
export SSH_AUTH_SOCK=$(gpgconf --list-dirs agent-ssh-socket)
# SSL
export CPRNG_SEED_SOURCE="jitterentropy"
export CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
export JENT_DISABLE_STIR=1
export JENT_DISABLE_UNBIAS=1
export JENT_DISABLE_MEMORY_ACCESS=1
export JENT_OSR=128
export FIPS_MODULE_PATH="/opt/qai/qompassl/lib64/ossl-modules/fips.so"
export FIPS_CONFIG_PATH="/opt/qai/qompassl/ssl/fipsmodule.cnf"
export SSL_CERT_DIR=/etc/ssl/certs
export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
export OPENSSL_ENGINES=/usr/lib/engines-3:/opt/qai/qompassl/lib64/engines-3
# export OPENSSL_ia32cap=""  # Uncomment and set value if needed
export CTLOG_FILE=/etc/ssl/ct_log_list.cnf
export OPENSSL_CONF=/etc/ssl/openssl.cnf
export OPENSSL_MODULES=/usr/lib/ossl-modules/:/opt/qai/qompassl/lib64/ossl-modules
export OSSL_MODULES=/opt/qai/qompassl/lib64/ossl-modules
export CRYPTOGRAPHY_OPENSSL_NO_LEGACY=1
# Tor
export TORSOCKS_CONF_FILE="$HOME/.config/sextant/torsocks.conf"
# Tmp
export TMPDIR="$HOME/.tmp"
# TPM
export TPM2TOOLS_TCTI="swtpm:device=unixio,path=$XDG_RUNTIME_DIR/swtpm/swtpm-sock"
export TPM2_PKCS11_STORE="$XDG_DATA_HOME/tpm2-pkcs11"
export TSS2_FAPICONF="$HOME/.config/tpm2-tss/fapi-config.json"
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

export PATH="${PATH:+$PATH:}/opt/qai/qompassl/bin"
export LD_LIBRARY_PATH="/opt/qai/qompassl/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

qompassl() {
  /opt/qai/qompassl/bin/qompassl "$@"
}

if [[ -z "$SSH_AUTH_SOCK" ]] || ! ssh-add -l >/dev/null 2>&1; then
  if command -v gpgconf >/dev/null 2>&1; then
    export SSH_AUTH_SOCK=$(gpgconf --list-dirs agent-ssh-socket)
  fi

  if ! ssh-add -l >/dev/null 2>&1; then
    eval $(ssh-agent -s)
    # ssh-add ~/.ssh/id_ed25519 2>/dev/null
  fi
fi

# Special directory check for pw-ssh
[[ ${PWD/$HOME\/.pw-ssh.sh\//} != ${PWD} ]] && exec ssh "$(basename "${PWD}")"

CURRENT_SHELL=$(basename "$SHELL")
export SOPS_AGE_KEY_FILE=~/.config/sops/age/keys.txt
setup_sops_env() {
  if [[ -f ~/.ssh/id_ed25519.enc ]]; then
    if command -v ssh-to-age >/dev/null 2>&1; then
      if [[ -f ~/.ssh/id_ed25519 ]]; then
        export SOPS_AGE_KEY=$(ssh-to-age -private-key <~/.ssh/id_ed25519 2>/dev/null)
      fi
    fi
  fi
  if [[ -n "$SOPS_PGP_FP" ]]; then
    export SOPS_PGP_FP="$SOPS_PGP_FP"
  fi
}
start_ssh_agent() {
  case "$CURRENT_SHELL" in
    fish)
      eval $(ssh-agent -c)
      ;;
    bash | zsh | *)
      eval $(ssh-agent -s)
      ;;
  esac
}
load_encrypted_keys() {
  setup_sops_env

  if [[ -f ~/.ssh/config.enc ]]; then
    sops -d ~/.ssh/config.enc >~/.ssh/config 2>/dev/null
    chmod 600 ~/.ssh/config
  fi
  for key_file in ~/.ssh/id_*.enc; do
    if [[ -f "$key_file" ]]; then
      key_name=$(basename "$key_file" .enc)

      temp_key="/tmp/${key_name}_$$"
      if sops -d "$key_file" >"$temp_key" 2>/dev/null; then
        chmod 600 "$temp_key"
        ssh-add "$temp_key" 2>/dev/null
        shred -u "$temp_key" 2>/dev/null || rm -f "$temp_key"
      fi
    fi
  done
}
if command -v sops >/dev/null 2>&1 && [[ -f ~/.ssh/id_ed25519.enc ]]; then
  if ! pgrep -x "ssh-agent" >/dev/null; then
    start_ssh_agent
  fi
  load_encrypted_keys
  case "$CURRENT_SHELL" in
    fish)
      echo "set -gx SSH_AUTH_SOCK $SSH_AUTH_SOCK"
      echo "set -gx SSH_AGENT_PID $SSH_AGENT_PID"
      ;;
    bash | zsh | *)
      echo "export SSH_AUTH_SOCK=$SSH_AUTH_SOCK"
      echo "export SSH_AGENT_PID=$SSH_AGENT_PID"
      ;;
  esac
fi
