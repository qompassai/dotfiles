<!-- #################################################################
<!-- /qompassai/dotfiles/.config/agent-ctrl/README.md
<!-- Qompass AI README
<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2026 Qompass AI
<!--
<!-- Licensed under the Apache License, Version 2.0 (the "License");
<!-- you may not use this file except in compliance with the License.
<!-- You may obtain a copy of the License at:
<!--   http://www.apache.org/licenses/LICENSE-2.0
<!--
<!-- Unless required by applicable law or agreed to in writing, software
<!-- distributed under the License is distributed on an "AS IS" BASIS,
<!-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
<!-- See the License for the specific language governing permissions and
<!-- limitations under the License.
<!-- #################################################################


# agent-ctrl configuration

This directory contains your agent-ctrl artifacts.
agent-ctrl is a CLI tool for managing AI agent configurations using a standard directory-based structure.
CLI tool repository: https://github.com/ahmet-cetinkaya/agent-ctrl

## Structure

- `rules/`: Behavioral rules in Markdown
- `skills/`: Skills using the SKILL.md standard
- `agents/`: Agent persona definitions
- `commands/`: Command prompt templates
- `.agent-ctrl/mcps/`: MCP server definitions
- `.agent-ctrl/.env`: SkillsMP and Smithery API credentials

## Next steps

1. Add your artifacts to the directories above.
2. Run `agent-ctrl rule ls`, `agent-ctrl skill ls`, or `agent-ctrl agent ls`.
3. Apply your configuration with `agent-ctrl apply <platform>`.
