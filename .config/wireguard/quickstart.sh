#!/usr/bin/env sh
# quickstart.sh
# Qompass AI - [Add description here]
# Copyright (C) 2025 Qompass AI, All rights reserved
#################################################### 
set -eu
KEYDIR=${1:-./wg-keys}
HOSTNAMES=${HOSTNAMES:-"caffe doppio pensare primo ristretto"}
shift || true
if [ "${HOSTNAMES:-}" ]; then
    :
elif [ $# -ge 1 ]; then
    HOSTNAMES="$*"
else
    printf "Enter space-separated hostnames (e.g.: caffe doppio pensare primo ristretto):\n> "
    read -r HOSTNAMES
fi
[ -z "$HOSTNAMES" ] && { echo "No hostnames given"; exit 1; }
mkdir -p "$KEYDIR"
chmod 700 "$KEYDIR"
if ! command -v wg >/dev/null 2>&1; then
    echo "❌ 'wg' not found. Install wireguard-tools first."
    exit 1
fi
echo
for HOST in $HOSTNAMES; do
    WG_PRIV="$KEYDIR/$HOST.privatekey"
    WG_PUB="$KEYDIR/$HOST.publickey"
    PSK="$KEYDIR/$HOST.presharedkey"
    umask 077
    [ -f "$WG_PRIV" ] || wg genkey > "$WG_PRIV"
    wg pubkey < "$WG_PRIV" > "$WG_PUB"
    [ -f "$PSK" ] || wg genpsk > "$PSK"
    chmod 600 "$WG_PRIV" "$PSK"
    chmod 644 "$WG_PUB"
    echo "✅ Keys for $HOST: $WG_PRIV $WG_PUB $PSK"
done
echo
echo "== WireGuard config snippets (per host) =="
for HOST in $HOSTNAMES; do
    WG_PRIV="$KEYDIR/$HOST.privatekey"
    WG_PUB="$KEYDIR/$HOST.publickey"
    PSK="$KEYDIR/$HOST.presharedkey"
    echo
    echo "---- $HOST ----"
    echo "[Interface]"
    echo "PrivateKey = $(cat "$WG_PRIV")"
    echo "# PublicKey (share with peers): $(cat "$WG_PUB")"
    echo "..."
    echo "[Peer example]"
    echo "PublicKey = <peer-public-key>"
    echo "PresharedKey = $(cat "$PSK")"
    echo "AllowedIPs = ..."
done
echo
echo "All keys stored in: $KEYDIR"
echo
exit 0
