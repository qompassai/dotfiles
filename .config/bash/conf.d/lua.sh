#!/usr/bin/env bash
# #################################################################
# /qompassai/dotfiles/.config/bash/conf.d/lua.sh
# Qompass AI Bash Lua Config
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Qompass AI
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# #################################################################
export BUILDCACHE_CONFIG_FILE="$XDG_CONFIG_HOME/buildcache/config.json"
export BUILDCACHE_DIR="$XDG_CACHE_HOME/buildcache"
export BUILDCACHE_LUA_PATH="$XDG_CONFIG_HOME/buildcache/lua"
export BUILDCACHE_CC=/usr/bin/clang
export BUILDCACHE_CXX=/usr/bin/clang++
#export BUILDCACHE_IMPERSONATE=/usr/bin/clang
#alias lua='lua5.1'


export PATH="$HOME/.local/bin:$HOME/.luarocks/bin:$PATH"
