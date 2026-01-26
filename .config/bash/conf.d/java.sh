#!/usr/bin/env bash
# /qompassai/dotfiles/.config/bash/conf.d/java.sh
# Qompass AI Bash Java Config
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------------------
export JAVA_HOME="/usr/lib/jvm/java-25-openjdk"
export PATH="$JAVA_HOME/bin:$PATH"
export _JAVA_OPTIONS="-Djava.util.prefs.userRoot=${XDG_CONFIG_HOME:-$HOME/.config}/java"
