#!/usr/bin/env bash
# #################################################################
# /qompassai/.config/dkms/modulelist.sh
# Qompass AI Modulelist
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
kernel_modules="/usr/lib/modules/$(uname -r)"

comm -23 \
  <(
    sed -E \
      's/:.*//; s|.*/||; s/\.ko(\.(gz|xz|zst))?$//; s/-/_/g' \
      "$kernel_modules/modules.dep" |
      sort -u
  ) \
  <(
    lsmod |
      awk 'NR > 1 { print $1 }' |
      sort -u
  )
