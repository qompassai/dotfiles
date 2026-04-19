#!/bin/bash
if ip link show | grep -q "tun\|gpd\|ppp"; then
    IP=$(ip -4 addr show tun0 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}' || echo "")
    echo "{\"text\":\"󰒃 VPN\", \"tooltip\":\"TDS VPN connected\\n$IP\", \"class\":\"connected\"}"
else
    echo "{\"text\":\"󰦞 VPN\", \"tooltip\":\"TDS VPN disconnected\\nClick to connect\", \"class\":\"disconnected\"}"
fi
