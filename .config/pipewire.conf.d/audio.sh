# audio.sh
# Qompass AI - [Add description here]
# Copyright (C) 2025 Qompass AI, All rights reserved
# ----------------------------------------
PKGS=(ir.lv2
	lib32-libsrtp
	plib
	popsift
	realtime-privileges
	realtime-suggestions
	rtaudio
	rtirq
	rt-tests
	schedtool
	trx
	)
for pkg in "${PKGS[@]}"; do
        yay -Sy "$pkg"
done
