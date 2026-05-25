#!/usr/bin/env bash

# qml.sh
# Qompass AI - [ ]
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
export QML_IMPORT_PATH="/usr/lib/qt6/qml:$HOME/.local/share/qml:$HOME/.config/qml"
export QML2_IMPORT_PATH="$QML_IMPORT_PATH"
export QMLLS_BUILD_DIRS="$HOME/build"
export QMLLS_NO_CMAKE_CALLS=1
export QT_PLUGIN_PATH="/usr/lib/qt6/plugins"
