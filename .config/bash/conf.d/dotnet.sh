# shellcheck shell=bash
# #################################################################
# /qompassai/.config/bash/conf.d/dotnet.sh
# Qompass AI Dotnet
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
# The CLI home and the NuGet package cache move into the XDG tree;
# without these, dotnet defaults to ~/.dotnet and ~/.nuget.
export DOTNET_CLI_HOME="${XDG_DATA_HOME:-$HOME/.local/share}/dotnet"
export DOTNET_CLI_TELEMETRY_OPTOUT=1
export DOTNET_NOLOGO=1
export NUGET_PACKAGES="${XDG_CACHE_HOME:-$HOME/.cache}/nuget/packages"
case ":$PATH:" in
    *":$DOTNET_CLI_HOME/tools:"*) ;;
    *) export PATH="$DOTNET_CLI_HOME/tools:$PATH" ;;
esac
# Legacy tools directory from the pre-XDG install; drop this block
# once the global tools are reinstalled under DOTNET_CLI_HOME.
case ":$PATH:" in
    *":$HOME/.dotnet/tools:"*) ;;
    *) export PATH="$HOME/.dotnet/tools:$PATH" ;;
esac
