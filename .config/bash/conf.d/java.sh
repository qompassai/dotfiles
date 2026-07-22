#!/usr/bin/env bash
# /qompassai/dotfiles/.config/bash/conf.d/java.sh
# Qompass AI Bash Java Config
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------------------
export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
export XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
if command -v archlinux-java > /dev/null 2>&1; then
    JAVA_DEFAULT=""
    if JAVA_DEFAULT="$(archlinux-java get 2> /dev/null)"; then
        if [[ -n $JAVA_DEFAULT && -d "/usr/lib/jvm/$JAVA_DEFAULT" ]]; then
            JAVA_HOME="/usr/lib/jvm/$JAVA_DEFAULT"
            export JAVA_HOME
        elif [[ -L /usr/lib/jvm/default ]]; then
            JAVA_HOME="$(readlink -f /usr/lib/jvm/default)"
            export JAVA_HOME
        fi
    fi
fi
export PATH="${JAVA_HOME:+$JAVA_HOME/bin:}$PATH"
export _JAVA_OPTIONS="-Djava.util.prefs.userRoot=$XDG_CONFIG_HOME/java"
export MAVEN_USER_HOME="$XDG_CONFIG_HOME/maven"
export MAVEN_ARGS="-Dmaven.repo.local=$XDG_DATA_HOME/maven/repository"


