#!/usr/bin/env bash

# patch.sh
# Qompass AI - [ ]
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
sudo sed -i 's/no_llseek/noop_llseek/g' /var/lib/dkms/winesync/5.16/source/src/drivers/misc/winesync.c
sudo dkms remove winesync/5.16 --all
sudo dkms install winesync/5.16 -k 6.19.8-zen1-1-zen
