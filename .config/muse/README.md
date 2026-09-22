<!-- #################################################################
<!-- /qompassai/.config/muse/README.md
<!-- Qompass AI Meta Muse Config Docs
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
<!-- ################################################################# -->
```

```

# Muse

`muse` is an interactive terminal coding agent.

If no subcommand is given, Muse starts the interactive TUI. Pass a prompt to start a session directly, or use one of the subcommands below.

```text
Usage: muse [OPTIONS] [PROMPT]
       muse [OPTIONS] <COMMAND>
```

## Commands

<details>
<summary><code>auth</code> — Store provider API credentials</summary>

```text
muse auth
```
</details>

<details>
<summary><code>config</code> — Validate enterprise configuration documents</summary>

```text
muse config
```
</details>

<details>
<summary><code>exec</code> — Run one prompt non-interactively (headless)</summary>

```text
muse exec
```
</details>

<details>
<summary><code>export</code> — Export a session transcript to a file</summary>

```text
muse export
```
</details>

<details>
<summary><code>init</code> — Scaffold agent configuration in this workspace</summary>

```text
muse init
```
</details>

<details>
<summary><code>login</code> — Log in to a provider</summary>

```text
muse login
```
</details>

<details>
<summary><code>logout</code> — Remove stored provider credentials</summary>

```text
muse logout
```
</details>

<details>
<summary><code>mcp</code> — Log in to or out of an MCP server (OAuth)</summary>

```text
muse mcp
```
</details>

<details>
<summary><code>resume</code> — Resume a previous session</summary>

```text
muse resume --last
muse resume <session-ref>
```
</details>

<details>
<summary><code>sandbox</code> — Check or set up the OS sandbox</summary>

```text
muse sandbox
```
</details>

<details>
<summary><code>schema</code> — Export the MSP wire schema</summary>

Exports JSON Schema or TypeScript.

```text
muse schema
```
</details>

<details>
<summary><code>serve</code> — Serve an MSP session host over standard input/output</summary>

```text
muse serve
```
</details>

<details>
<summary><code>session-message</code> — List or send cross-session messages</summary>

```text
muse session-message
```
</details>

<details>
<summary><code>skills</code> — List, inspect, enable, or disable skills</summary>

```text
muse skills
```
</details>

<details>
<summary><code>trace</code> — Inspect a recorded session or run trace</summary>

```text
muse trace
```
</details>

## Options

<details>
<summary><code>--agents &lt;JSON&gt;</code></summary>

Supply one ephemeral agent-definition overlay.
</details>

<details>
<summary><code>--approval-judge &lt;off|on&gt;</code></summary>

Enable or disable the LLM approval judge for prompt-bound calls.

```text
Default: on
```
</details>

<details>
<summary><code>--approval-mode &lt;MODE&gt;</code></summary>

Select the tool approval mode.

```text
Accepted values: untrusted | on-request | never
Default: on-request
```
</details>

<details>
<summary><code>--base-url &lt;URL&gt;</code></summary>

Override the Meta provider base URL.
</details>

<details>
<summary><code>--disable-approval</code></summary>

Disable tool approval prompts for this workspace run.
</details>

<details>
<summary><code>--disable-sandbox</code></summary>

Disable shell filesystem and network sandboxing for this run.
</details>

<details>
<summary><code>--disable-shell</code></summary>

Disable workspace shell execution.
</details>

<details>
<summary><code>--disable-write</code></summary>

Disable non-shell workspace filesystem writes.
</details>

<details>
<summary><code>--echo-delay-ms &lt;MS&gt;</code></summary>

Set the deterministic echo reply delay in milliseconds.

```text
Available with: echo provider only
```
</details>

<details>
<summary><code>--enable-shell-tool</code></summary>

Use the legacy shell tool instead of the managed platform shell.
</details>

<details>
<summary><code>-h</code>, <code>--help</code></summary>

Print help.
</details>

<details>
<summary><code>--image &lt;PATH&gt;</code></summary>

Attach a local image file to the next submitted prompt.
</details>

<details>
<summary><code>--model &lt;MODEL&gt;</code></summary>

Set the model ID for non-echo providers.
</details>

<details>
<summary><code>--no-parallel-tool-calls</code></summary>

Disable Meta API parallel tool calls.
</details>

<details>
<summary><code>--no-session-log</code></summary>

Do not persist session event logs to disk.
</details>

<details>
<summary><code>--parallel-tool-calls</code></summary>

Enable Meta API parallel tool calls.
</details>

<details>
<summary><code>--permission-profile &lt;ID&gt;</code></summary>

Select a named permission profile for this session.
</details>

<details>
<summary><code>--preset &lt;NAME&gt;</code></summary>

Run a built-in preset.

```text
Accepted values: native-basic | miniswe
```
</details>

<details>
<summary><code>--provider &lt;MODE&gt;</code></summary>

Set the startup provider.

```text
Accepted values: echo | meta
Default: meta
```
</details>

<details>
<summary><code>--reasoning-effort &lt;EFFORT&gt;</code></summary>

Set the Meta provider reasoning effort.

```text
Accepted values: none | minimal | low | medium | high | xhigh | max | ultra
Default: high
```
</details>

<details>
<summary><code>--sandbox-network &lt;MODE&gt;</code></summary>

Set the sandbox network mode.

```text
Accepted values: restricted | enabled | proxy-only
Default: proxy-only
```
</details>

<details>
<summary><code>--subagent-worktree-isolation</code></summary>

Compatibility flag for subagent worktree isolation. The capability defaults to enabled; only an affirmative per-child request asks for isolation. Requests can be rejected when capability, provider, or Git prerequisites are unavailable.
</details>

<details>
<summary><code>--trust-workspace</code></summary>

Trust this workspace for the current run, allowing its skills and rules to load. This does not save trust persistently.
</details>

<details>
<summary><code>-V</code>, <code>--version</code></summary>

Print the Muse version.
</details>

<details>
<summary><code>-w</code>, <code>--worktree [MODE]</code></summary>

Select Git worktree behavior for the session.

```text
Accepted values: off | create | existing
Default: off
Bare -w: create
```
</details>

<details>
<summary><code>--worktree-base &lt;REF&gt;</code></summary>

Set the base Git reference for `--worktree create`.

```text
Default: HEAD
```
</details>

<details>
<summary><code>--worktree-existing &lt;PATH&gt;</code></summary>

Set the existing worktree path used by `--worktree existing`.
</details>

<details>
<summary><code>--workspace &lt;PATH&gt;</code></summary>

Register policy-gated workspace tools rooted at `PATH`.
</details>

<details>
<summary><code>--yolo</code></summary>

Disable approval and sandboxing and trust this workspace for this run.

> [!WARNING]
> This disables both approval and sandbox protections for the session.
</details>

## Safety defaults

Muse enables tool approval and the sandbox by default.

| Control | Default | Override |
| --- | --- | --- |
| Tool approval | `on-request` | `--approval-mode`, `--disable-approval`, or `--yolo` |
| Shell filesystem/network sandbox | Enabled | `--disable-sandbox` or `--yolo` |
| Sandbox network | `proxy-only` | `--sandbox-network restricted`, `enabled`, or `proxy-only` |
| Session logs | Persisted | `--no-session-log` |
| Workspace trust | Not persistent | `--trust-workspace` or `--yolo` |

## Examples

```bash
# Start an interactive session.
muse

# Start an interactive session with an initial prompt.
muse 'Review the current workspace and identify the highest-priority issue.'

# Run one prompt without the TUI.
muse exec 'Run the test suite and summarize failures.'

# Resume the most recent session.
muse resume --last

# Create an isolated Git worktree for a session.
muse --worktree create 'Implement the requested change and run tests.'

# Use a named permission profile.
muse --permission-profile review 'Review this pull request.'
```
