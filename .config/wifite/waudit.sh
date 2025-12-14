#!/usr/bin/env bash
# /qompassai/dotfiles/.config/wifit/waudit.sh
# Qompass AI Wifite Wordy Audit
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
WORDLIST="${XDG_DATA_HOME}/wifite/wordy.txt"
wifite --wpa --dict "$WORDLIST" --clients-only --new-hs --skip-crack >"$XDG_DATA_HOME/wifite/wpa-crack.txt"
