# /qompassai/Shell/.profile.d/17-qpg.fish
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
#set -gx C_INCLUDE_PATH "/opt/qai/liboqs/include"(test -n "$C_INCLUDE_PATH"; and echo :$C_INCLUDE_PATH)
#set -gx LIBRARY_PATH "/opt/qai/liboqs/lib"(test -n "$LIBRARY_PATH"; and echo :$LIBRARY_PATH)
#set -gx LD_LIBRARY_PATH "/opt/qai/liboqs/lib"(test -n "$LD_LIBRARY_PATH"; and echo :$LD_LIBRARY_PATH)
#set -gx LIBOQS_INCLUDE_DIR "/opt/qai/liboqs/include/oqs"
#set -gx LIBOQS_LIB_DIR "/opt/qai/liboqs/lib"
#set -gx PKG_CONFIG_PATH "/opt/qai/liboqs/lib/pkgconfig"(test -n "$PKG_CONFIG_PATH"; and echo :$PKG_CONFIG_PATH)
set -gx SSH_AUTH_SOCK (gpgconf --list-dirs agent-ssh-socket)
set -gx SSLKEYLOGFILE /tmp/sslkeylog.log
set -gx GPG_TTY (tty)
set -gx PASSWORD_STORE_DIR "$HOME/.password-store"
set -gx CPRNG_SEED_SOURCE jitterentropy
set -gx CURL_CA_BUNDLE /etc/ssl/certs/ca-certificates.crt
set -gx JENT_DISABLE_STIR 1
set -gx JENT_DISABLE_UNBIAS 1
set -gx JENT_DISABLE_MEMORY_ACCESS 1
set -gx JENT_OSR 128
#set -gx FIPS_MODULE_PATH "/opt/qai/qompassl/lib64/ossl-modules/fips.so"
#set -gx FIPS_CONFIG_PATH "/opt/qai/qompassl/ssl/fipsmodule.cnf"
set -gx SSL_CERT_DIR /etc/ssl/certs
set -gx SSL_CERT_FILE /etc/ssl/certs/ca-certificates.crt
set -gx OPENSSL_ENGINES "/usr/lib/engines-3:/opt/qai/qompassl/lib64/engines-3"
set -gx CTLOG_FILE /etc/ssl/ct_log_list.cnf
set -gx OPENSSL_CONF /etc/ssl/openssl.cnf
set -gx OPENSSL_MODULES "/usr/lib/ossl-modules/:/opt/QAI/qompassl/lib64/ossl-modules"
#set -gx OSSL_MODULES /opt/qai/qompassl/lib64/ossl-modules
set -gx CRYPTOGRAPHY_OPENSSL_NO_LEGACY 1
set -gx TORSOCKS_CONF_FILE "$HOME/.config/sextant/torsocks.conf"
set -gx TMPDIR "$HOME/.tmp"
set -gx TPM2TOOLS_TCTI "swtpm:device=unixio,path=$XDG_RUNTIME_DIR/swtpm/swtpm-sock"
set -gx TPM2_PKCS11_STORE "$XDG_DATA_HOME/tpm2-pkcs11"
set -gx TSS2_FAPICONF "$HOME/.config/tpm2-tss/fapi-config.json"
set -gx LANG "en_US.UTF-8"
set -gx LC_ALL "en_US.UTF-8"
