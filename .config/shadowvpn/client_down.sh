#!/usr/bin/env sh
# /qompassai/dotfiles/.config/shadowvpn/client_down.sh
# Qompass AI ShadowVPN Client Down Script
# Copyright (C) 2025 Qompass AI, All rights reserved
#################################################
#sysctl -w net.ipv4.ip_forward=0
iptables -t nat -D POSTROUTING -o $intf -j MASQUERADE
iptables -D FORWARD -i $intf -m state --state RELATED,ESTABLISHED -j ACCEPT
iptables -D FORWARD -o $intf -j ACCEPT
ip route del $server
ip route del   0/1
ip route del 128/1
echo $0 done
