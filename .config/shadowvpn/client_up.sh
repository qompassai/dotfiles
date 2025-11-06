#!/bin/sh
# /qompassai/dotfiles/.config/shadowvpn/client_up.sh
# Qompass AI ShadowVPN Client Up Script
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
sysctl -w net.ipv4.ip_forward=1
ip addr add $net dev $intf
ip link set $intf mtu $mtu
ip link set $intf up
iptables -t nat -A POSTROUTING -o $intf -j MASQUERADE
iptables -I FORWARD 1 -i $intf -m state --state RELATED,ESTABLISHED -j ACCEPT
iptables -I FORWARD 1 -o $intf -j ACCEPT
ip route add   0/1 dev $intf
ip route add 128/1 dev $intf
echo $0 done
