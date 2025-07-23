#!/usr/bin/env sh
# /qompassai/Shell/.profile.d/60-tor.sh
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################

export ARTI_CACHE_DIR="$HOME/.cache/arti"
export ARTI_CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/arti"
export ARTI_DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/arti"
export NYX_CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/nyx"
export ONIONSHARE_CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/onionshare"
export TORBROWSER_HOME="$HOME/.local/share/torbrowser"
export TOR_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}/sextant"
export TOR_DATA_HOME="$TOR_CONFIG_HOME/data"
export TOR_HIDDEN_SERVICE_DIR="$TOR_DATA_HOME/hidden_service"
export TOR_IPV4=$(ip route get 1.1.1.1 2>/dev/null | awk '/src/ {print $NF; exit}')
export TOR_IPV6=$(ip -6 addr show scope global | awk '/inet6/ {print $2}' | cut -d/ -f1 | head -n1)
export TOR_LOG_DIR="$TOR_DATA_HOME/logs"
export TOR_SOCKS_PORT="9050"
#export ALL_PROXY="socks5://127.0.0.1:$TOR_SOCKS_PORT"
#export HTTP_PROXY="http://127.0.0.1:8118"
#export HTTPS_PROXY="http://127.0.0.1:8118"
#export SOCKS_PROXY="socks5://127.0.0.1:$TOR_SOCKS_PORT"
mkdir -p "$TOR_DATA_HOME" "$TOR_LOG_DIR" "$TOR_HIDDEN_SERVICE_DIR"
mkdir -p "$ARTI_CONFIG_DIR" "$ARTI_CACHE_DIR" "$ARTI_DATA_DIR"
mkdir -p "$NYX_CONFIG_DIR" "$ONIONSHARE_CONFIG_DIR"

chmod 700 "$TOR_DATA_HOME" "$TOR_HIDDEN_SERVICE_DIR" "$TOR_LOG_DIR"
chmod 700 "$ARTI_CONFIG_DIR" "$ARTI_CACHE_DIR" "$ARTI_DATA_DIR"

TEMPLATE="$TOR_CONFIG_HOME/torrc.template"
FINAL="$TOR_CONFIG_HOME/torrc"
if [ -f "$TEMPLATE" ]; then
    envsubst < "$TEMPLATE" > "$FINAL"
    chmod 600 "$FINAL"
fi
torcheck_full() {
    echo "=== Tor Connectivity Check ==="
    echo "Direct IP:"
    curl -s https://ipinfo.io/ip 2>/dev/null || echo "Direct connection failed"
    echo ""
    echo "Tor IP:"
    curl --socks5 127.0.0.1:9050 -s https://ipinfo.io/ip 2>/dev/null || echo "Tor connection failed"
    echo ""
    echo "Tor Project Check:"
    curl --socks5 127.0.0.1:9050 -s https://check.torproject.org/api/ip | grep -o '"IsTor":[^,]*' || echo "Tor check failed"
}

tornewidentity() {
    echo "Requesting new Tor identity..."
    if command -v nc >/dev/null; then
        echo -e 'AUTHENTICATE ""\r\nSIGNAL NEWNYM\r\nQUIT' | nc 127.0.0.1 9051
        echo "New identity requested. Wait 10 seconds for circuit rebuild."
        sleep 10
        torcheck_full
    else
        echo "netcat (nc) not found. Install netcat to use this function."
    fi
}

create_onion_service() {
    local service_name="${1:-default}"
    local local_port="${2:-80}"
    local onion_port="${3:-80}"

    if [ -z "$1" ]; then
        echo "Usage: create_onion_service <service_name> [local_port] [onion_port]"
        echo "Example: create_onion_service mywebsite 8080 80"
        return 1
    fi

    local service_dir="$TOR_HIDDEN_SERVICE_DIR/$service_name"
    mkdir -p "$service_dir"
    chmod 700 "$service_dir"

    if ! grep -q "HiddenServiceDir $service_dir" "$FINAL" 2>/dev/null; then
        echo "" >> "$FINAL"
        echo "# Hidden Service: $service_name" >> "$FINAL"
        echo "HiddenServiceDir $service_dir" >> "$FINAL"
        echo "HiddenServicePort $onion_port 127.0.0.1:$local_port" >> "$FINAL"
        echo "Onion service '$service_name' added to torrc."
        echo "Restart Tor to activate: systemctl --user restart tor"
        echo "Onion address will be in: $service_dir/hostname"
    else
        echo "Service '$service_name' already exists."
    fi
}

show_onion_addresses() {
    echo "=== Onion Service Addresses ==="
    if [ -d "$TOR_HIDDEN_SERVICE_DIR" ]; then
        for service in "$TOR_HIDDEN_SERVICE_DIR"/*/; do
            if [ -d "$service" ]; then
                service_name=$(basename "$service")
                hostname_file="$service/hostname"
                if [ -f "$hostname_file" ]; then
                    echo "$service_name: $(cat "$hostname_file")"
                else
                    echo "$service_name: (not yet generated - restart Tor)"
                fi
            fi
        done
    else
        echo "No onion services configured."
    fi
}

arti_start() {
    echo "Starting Arti (Rust Tor implementation)..."
    if command -v arti >/dev/null; then
        arti proxy --config-dir "$ARTI_CONFIG_DIR" --cache-dir "$ARTI_CACHE_DIR"
    else
        echo "Arti not found. Install with: cargo install arti"
    fi
}

tor_monitor() {
    if command -v nyx >/dev/null; then
        nyx
    else
        echo "Nyx not found. Install with: pip install nyx"
    fi
}

onion_share() {
    local file_or_dir="$1"
    if [ -z "$file_or_dir" ]; then
        echo "Usage: onion_share <file_or_directory>"
        return 1
    fi

    if command -v onionshare-cli >/dev/null; then
        onionshare-cli --receive --public "$file_or_dir"
    else
        echo "OnionShare CLI not found. Install OnionShare."
    fi
}

tor_versions() {
    echo "=== Tor Ecosystem Versions ==="
    command -v tor >/dev/null && echo "Tor: $(tor --version | head -1)"
    command -v arti >/dev/null && echo "Arti: $(arti --version)"
    command -v nyx >/dev/null && echo "Nyx: $(nyx --version 2>/dev/null || echo 'Available')"
    command -v onionshare >/dev/null && echo "OnionShare: $(onionshare --version)"
    command -v torsocks >/dev/null && echo "Torsocks: $(torsocks --version | head -1)"
}

export -f torcheck_full tornewidentity create_onion_service show_onion_addresses
export -f arti_start tor_monitor onion_share tor_versions

