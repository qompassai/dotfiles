#!/usr/bin/env bash
# #################################################################
# /qompassai/.config/mdbook/quickstart.sh
# Qompass AI MDBook Quickstart
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

set -euo pipefail
XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
TEMPLATE_DIR="$XDG_CONFIG_HOME/mdbook"
TEMPLATE_BOOK_TOML="$TEMPLATE_DIR/book.toml"
PROJECT_ROOT="$(pwd)"
if [ ! -f "$TEMPLATE_BOOK_TOML" ]; then
  echo "mdBook template not found at: $TEMPLATE_BOOK_TOML" >&2
  exit 1
fi
mkdir -p "$PROJECT_ROOT/docs/book/src" "$PROJECT_ROOT/docs/book/theme"
cp "$TEMPLATE_BOOK_TOML" "$PROJECT_ROOT/docs/book/book.toml"
# The template book.toml references theme/book.css and theme/book.js via
# [output.html] additional-css/additional-js; mdBook fails the build if
# they are absent, so the theme travels with the config.
cp -a "$TEMPLATE_DIR/theme/." "$PROJECT_ROOT/docs/book/theme/"
echo "Copied template book.toml to $PROJECT_ROOT/docs/book/book.toml"
echo "Copied template theme to $PROJECT_ROOT/docs/book/theme/"
echo "You can now edit docs/book/book.toml for project-specific overrides."
