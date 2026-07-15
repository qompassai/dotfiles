#!/usr/bin/env bash
# /qompassai/dotfiles/.config/bash/conf.d/cmake.sh
# Qompass AI Bash CMake Script
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
export CMAKE_POLICY_VERSION_MINIMUM=4.4.0
export NINJA_DEFAULT_THROTTLE_RATES='{"anon":"100/hour","user":"1000/hour","burst":"60/min","sustained":"1000/day"}'
export NINJA_FIX_REQUEST_FILES_METHODS='["PUT","PATCH"]'
export NINJA_NUM_PROXIES=1
export NINJA_PAGINATION_CLASS="ninja.pagination.LimitOffsetPagination"
export NINJA_PAGINATION_PER_PAGE="100"
export NINJA_MAX_PER_PAGE_SIZE="200"
export NINJA_PAGINATION_MAX_LIMIT="1000"
export DJANGO_SETTINGS_MODULE="django.conf.global_settings"
#vim: set filetype=sh:
