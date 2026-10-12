#!/usr/bin/env bash

# python.sh
# Qompass AI Bash Python Config
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
# PYTHON_HISTORY is read by Python 3.13+ (it replaces the
# ~/.python_history default). The uv paths are uv's own XDG
# defaults, set explicitly per the house rule.
export PYTHON_HISTORY="${XDG_STATE_HOME:-$HOME/.local/state}/python/history"
export PYTHONNOUSERSITE=1
export UV_CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/uv"
export UV_PYTHON_INSTALL_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/uv/python"
export UV_TOOL_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/uv/tools"
#alias pip='python -m pip'
