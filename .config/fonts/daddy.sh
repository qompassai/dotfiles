#!/usr/bin/env bash
# daddy
# Qompass AI - [ ]
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
export XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
mkdir -p "$XDG_DATA_HOME/fonts/DaddyTimeMonoNF"
cd "$XDG_DATA_HOME/fonts/DaddyTimeMonoNF"

wget https://github.com/ryanoasis/nerd-fonts/releases/latest/download/DaddyTimeMono.tar.xz
tar xf DaddyTimeMono.tar.xz
rm DaddyTimeMono.tar.xz
mkdir -p "$HOME/.config/fontconfig/conf.d"

cat > "$HOME/.config/fontconfig/conf.d/50-local-nerd-fonts.conf" <<EOF
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <dir>$XDG_DATA_HOME/fonts</dir>
</fontconfig>
EOF

fc-cache -r "$XDG_DATA_HOME/fonts"
cp "$XDG_DATA_HOME/fonts/DaddyTimeMonoNF/DaddyTimeMonoNerdFontMono-Regular.ttf" \
   "$HOME/.termux/font.ttf"

termux-reload-settings
