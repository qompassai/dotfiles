#!/usr/bin/env bash
# ~/qompassai/dotfiles/.config/unbound/rpz/update-rpz.sh
# Copyright (C) 2025 Qompass AI, All rights reserved
# --------------------------------------------------
RPZ_DIR="/home/$USER/.config/unbound/rpz"
TEMP_DIR="/tmp/rpz-update"
MALWARE_ZONE="$RPZ_DIR/malware.zone"

mkdir -p "$TEMP_DIR"

echo "Updating RPZ threat intelligence..."

curl -s "https://malware-filter.gitlab.io/malware-filter/urlhaus-filter-dnscrypt-blocked-names.txt" \
    | grep -v '^#' | grep -v '^$' > "$TEMP_DIR/malware-domains.txt"

{
    echo '$TTL 60'
    echo '@ IN SOA localhost. admin.localhost. ('
    echo "    $(date +%Y%m%d%H)  ; Serial"
    echo '    3600        ; Refresh'
    echo '    1800        ; Retry'
    echo '    604800      ; Expire'
    echo '    60          ; Minimum TTL'
    echo ')'
    echo ''

    while read -r domain; do
        [ -n "$domain" ] && echo "$domain CNAME ."
    done < "$TEMP_DIR/malware-domains.txt"

} > "$TEMP_DIR/new-malware.zone"
if unbound-checkconf -f "$TEMP_DIR/new-malware.zone"; then
    cp "$TEMP_DIR/new-malware.zone" "$MALWARE_ZONE"
    chown unbound:unbound "$MALWARE_ZONE"
    systemctl reload unbound
    echo "RPZ updated successfully"
else
    echo "RPZ validation failed"
fi
rm -rf "$TEMP_DIR"
