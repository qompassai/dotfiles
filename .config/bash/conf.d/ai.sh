#!/usr/bin/env bash
# ai.sh
# Qompass AI - AI tooling environment
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
export AI_SKILLS_DIR="$XDG_CONFIG_HOME/skills"
mkdir -p "$AI_SKILLS_DIR"
# Persistent kernel caches (kept off the /tmp tmpfs); formerly in
# ~/.bashrc, moved here with the rest of the AI environment.
export TORCHINDUCTOR_CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/torchinductor"
export TRITON_CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/triton"
