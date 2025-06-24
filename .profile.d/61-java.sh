#!/usr/bin/env sh
# /qompassai/Shell/.profile.d/61-java.sh
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################

# Remove or comment out the following if you want to always use GraalVM:
# eval "$(cs java --jvm 17 --env)"
export COURSIER_BIN_DIR="$HOME/.local/share/coursier/bin"
export COURSIER_CACHE="$HOME/.cache/coursier"
export COURSIER_CONFIG_DIR="$HOME/.config/coursier"
export COURSIER_CREDENTIALS="$HOME/.config/coursier/credentials"
export COURSIER_EXPERIMENTAL=1
export COURSIER_MODE=offline
export COURSIER_NO_TERM=1
export COURSIER_PROGRESS=0
export COURSIER_REPOSITORIES="central|https://repo1.maven.org/maven2"
export JAVA_HOME="/usr/lib/jvm/java-21-graalvm-ee"
export PATH="$JAVA_HOME/bin:$PATH"
export PATH="$PATH:$HOME/.local/share/coursier/bin"

