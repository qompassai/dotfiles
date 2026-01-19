#!/usr/bin/env sh
# /qompassai/dotfiles/.config/shadowvpn/server_up.sh
# Qompass AI ShadowVPN Server Up Script
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
sysctl -w net.ipv4.ip_forward=1
ip addr add $net dev $intf
ip link set $intf mtu $mtu
ip link set $intf up
if !(iptables-save -t nat | grep -q "shadowvpn"); then
  iptables -t nat -A POSTROUTING -s $net ! -d $net -m comment --comment "shadowvpn" -j MASQUERADE
fi
iptables -A FORWARD -s $net -m state --state RELATED,ESTABLISHED -j ACCEPT
iptables -A FORWARD -d $net -j ACCEPT
iptables -t mangle -A FORWARD -p tcp -m tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu
echo $0 done
