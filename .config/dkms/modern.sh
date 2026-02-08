#!/usr/bin/env bash

# modern.sh
# Qompass AI - [ ]
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
sudo rm /usr/src/linux
sudo ln -sf /usr/lib/modules/$(uname -r)/build /usr/src/linux
pacman -Q | grep headers
