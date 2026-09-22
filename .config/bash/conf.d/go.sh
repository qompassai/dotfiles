# #################################################################
# /qompassai/.config/bash/conf.d/go.sh
# Qompass AI Go
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
export GOPATH="${GOPATH:-${XDG_DATA_HOME:-$HOME/.local/share}/go}"
export GOBIN="${GOBIN:-${XDG_BIN_HOME:-$HOME/.local/bin}}"
export GOCACHE="${GOCACHE:-${XDG_CACHE_HOME:-$HOME/.cache}/go-build}"
export GOMODCACHE="${GOMODCACHE:-${XDG_CACHE_HOME:-$HOME/.cache}/go-mod}"
case " ${GOFLAGS-} " in
  *" -modcacherw "*) ;;
  *) export GOFLAGS="${GOFLAGS:+$GOFLAGS }-modcacherw" ;;
esac
mkdir -p "$GOBIN" "$GOCACHE" "$GOMODCACHE"
case ":$PATH:" in
  *":$GOBIN:"*) ;;
  *) export PATH="$GOBIN:$PATH" ;;
esac
export GOTOOLCHAIN="${GOTOOLCHAIN:-auto}"

