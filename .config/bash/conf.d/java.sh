#!/usr/bin/env bash
# /qompassai/dotfiles/.config/bash/conf.d/java.sh
# Qompass AI Bash Java Config
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------------------
# Gradle's user home moves into the XDG tree (it defaulted to
# ~/.gradle). MAVEN_USER_HOME was removed: Maven has no such
# variable; the local repository is set via MAVEN_ARGS below.
export GRADLE_USER_HOME="${XDG_DATA_HOME:-$HOME/.local/share}/gradle"
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
if [[ -n ${JAVA_HOME:-} ]]; then
    case ":$PATH:" in
        *":$JAVA_HOME/bin:"*) ;;
        *) export PATH="$JAVA_HOME/bin:$PATH" ;;
    esac
fi
export MAVEN_ARGS="-Dmaven.repo.local=${XDG_DATA_HOME:-$HOME/.local/share}/maven/repository"
export _JAVA_OPTIONS="-Djava.util.prefs.userRoot=${XDG_CONFIG_HOME:-$HOME/.config}/java"
