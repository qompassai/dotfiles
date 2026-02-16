#!/usr/bin/env bash
# /qompassai/dotfiles/.config/bash/conf.d/java.sh
# Qompass AI Bash Java Config
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------------------
export JAVA_HOME="/usr/lib/jvm/java-25-openjdk"
export PATH="$PATH:$JAVA_HOME/bin"
export _JAVA_OPTIONS="-Djava.util.prefs.userRoot=${XDG_CONFIG_HOME:-$HOME/.config}/java"
export MAVEN_USER_HOME="${XDG_CONFIG_HOME:-$HOME/.config}/maven"
export MAVEN_OPTS="-Dmaven.repo.local=${XDG_DATA_HOME:-$HOME/.local/share}/maven/repository"
