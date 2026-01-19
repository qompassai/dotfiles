#!/bin/bash
cd ~/.config/valkey

# Load secrets from SOPS
eval $(sops --decrypt secrets.enc.env)

# Start Valkey server
valkey-server valkey.conf
