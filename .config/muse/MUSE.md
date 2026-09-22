# Muse Code portable settings

Target: Muse Code **1.3.0-R3401.1**, matching your Arch `muse-code-bin` installation. Your selected defaults are **Dark** and **Xhigh**; this template adds local-first workflow guidance without disabling approval or sandbox controls.

## Files and installation

- **settings.json**: The portable configuration. No comments, credentials, usernames, absolute workstation paths, remote endpoints, or automatic package downloads.
- **muse-local**: An optional POSIX launcher that supplies actual environment defaults before starting Muse.
- **README.md**: Documentation kept outside strict JSON rather than adding unrecognized comment fields.

Muse resolves user settings under `$XDG_CONFIG_HOME/muse` when set, otherwise under `~/.config/muse`. Relaunch Muse after installing the settings; project guidance can override user guidance. ([Configuration documentation](https://dev.meta.ai/docs/muse-code/configuration))

From the directory containing the downloaded files:

```sh
config_dir="${XDG_CONFIG_HOME:-$HOME/.config}/muse"
mkdir -p "$config_dir"

# Review/merge existing settings rather than silently replacing them.
if [ -e "$config_dir/settings.json" ]; then
    printf '%s\n' "Existing settings found: $config_dir/settings.json"
    printf '%s\n' "Merge the template with your current settings manually."
else
    install -m 600 settings.json "$config_dir/settings.json"
fi
```

The configuration alone is usable. To ensure the environment preferences are inherited rather than merely included in agent guidance:

```sh
mkdir -p "$HOME/.local/bin"
install -m 755 muse-local "$HOME/.local/bin/muse-local"
"$HOME/.local/bin/muse-local"
```

Use `muse-local` instead of `muse` when you want those exports. It forwards arguments unchanged, does not change directories, and preserves the inherited PATH, locale, and terminal type.

## Preference settings

| Setting | Value | Purpose |
|---|---|---|
| `schema_version` | `1` | Required settings format version. |
| `reasoning_effort` | `"xhigh"` | Your persistent main-session reasoning preference. |
| `tui.terminal_background` | `"dark"` | Consistent dark theme rather than automatic detection. |

The exact effort and theme fields were checked against the embedded settings reference in the matching binary. Launch flags can override saved reasoning effort; the public documentation also describes `--reasoning-effort` and `/effort`. ([Configuration documentation](https://dev.meta.ai/docs/muse-code/configuration))

No model is pinned because you did not request one. Xhigh is not a promise that every background observer uses Xhigh; observers have their own runtime configuration.

## MCP integration structure

`mcpServers.local-observer` is an intentionally **disabled** local stdio example, not an installed MCP implementation. Replace `muse-local-observer` with a trusted, locally installed server executable, set its arguments and environment, then change `enabled` to `true`.

- **`transport: "stdio"`**: Start a local server process.
- **`command`**: Resolve an installed executable through PATH; do not put shell syntax in this field.
- **`args`**: Pass arguments as separate strings.
- **`env`**: Supply server-specific environment values only when needed.
- **`mode: "optional"`**: Allow startup to continue if the integration is unavailable.
- **`enabled: false`**: Avoid launching a nonexistent placeholder on a new workstation.

These transport fields, optional startup behavior, and `${VAR}` interpolation are documented by Meta. `/mcp` shows the connected server/tool inventory after startup. ([MCP documentation](https://dev.meta.ai/docs/muse-code/extending))

This template uses `mcpServers`, the canonical spelling found in and accepted by the tested 1.3.0 build. The public page uses `mcp_servers`; do not add a duplicate block under that spelling.

For a machine-specific executable path, replace the command with `${MUSE_LOCAL_OBSERVER_BIN}` and export that variable before launching Muse. Keep the server disabled until the variable and executable exist; do not rely on missing-variable handling.

A local process is not automatically read-only or offline. Choose a server with genuinely restricted tools and access, and remember that MCP tools are not made safe merely by their names.

## Documented hooks block

`hooks.SessionStart` contains one command handler. It uses `printf` to emit JSON containing `hookSpecificOutput.additionalContext`; the matching binary accepted this output and recorded a successful context effect during the smoke test.

The injected guidance requests:

- **Local discovery first**: Consult repository files, local project memory, and installed skills before external discovery.
- **Observation before mutation**: Prefer read-only inspection and verify changes using local checks.
- **Terminal defaults**: Use `EDITOR=nvim`, `VISUAL=nvim`, `PAGER=cat`, and `GIT_PAGER=cat`.
- **Explicit safety boundaries**: Seek approval for external publication, destructive actions, and credential access.

The hook is self-contained and does not source shell startup files, execute repository scripts, read credentials, install packages, or write to the filesystem. Its instructions are advisory, not a security enforcement mechanism.

### Why environment setup also has a launcher

A hook subprocess cannot export variables back into its parent Muse process. Consequently, the settings hook supplies pre-run instructions, while `muse-local` performs real environment setup before `exec muse`.

Neovim is an assumed installed dependency, reflecting your editor preference; install it separately or change both editor values. Do not force `TERM=xterm-256color` or modify PATH blindly, since those could misrepresent or break the host environment.

Meta documents user hooks in settings and session-start lifecycle hooks, with validation at startup. Hook changes require a new session. ([Hook documentation](https://dev.meta.ai/docs/muse-code/extending))

## Runtime capabilities

Each entry is an object with `enabled: true`, not a bare boolean. The identifiers were checked against the matching binary's bundled reminder manifest and settings reference.

| Capability key under `runtime_capabilities` | Intended role |
|---|---|
| `plugin:tbh-reminders:reminder:memory` | Surface relevant local memory. |
| `plugin:tbh-reminders:reminder:skill-reminder` | Surface relevant installed skills. |
| `plugin:tbh-reminders:reminder:goal-reminder` | Keep work aligned with the declared goal. |
| `plugin:tbh-reminders:reminder:verify-reminder` | Check completion and verification claims. |

These correspond to Meta's documented memory recall, skill recall, goal tracking, and verification observers; runtime gates can still affect their availability. ([Observer documentation](https://dev.meta.ai/docs/muse-code/extending))

This enables the requested observer set; JSON key order does not establish scheduling priority. Local-first priority is expressed by the startup guidance and the absence of an enabled remote MCP server, not by an invented `priority` field.

“Local-first” here means local evidence and tools first, **not local-only model inference**. This configuration does not select a local model, block network egress, prevent provider transmission, or guarantee that every observer executes on every run; observer model calls can incur additional usage. ([Observer usage discussion](https://codersera.com/blog/muse-code-complete-guide-2026/))

## Validation and portability

The following checks were performed in an isolated configuration/data directory:

- **JSON parsing**: Passed.
- **Launcher syntax**: `sh -n` passed.
- **Version match**: Downloaded the matching official Linux build and checked its SHA-256 against its release manifest.
- **Offline startup**: `exec --provider echo --max-model-steps 1` exited successfully with the template.
- **Hook execution**: Session log recorded `SessionStart`, exit code `0`, and `effects: ["context"]`; the supplied guidance appeared in runtime context.
- **No provider inference test**: The echo test does not validate Meta model access, billing, rendered TUI colors, or all observer behavior.
- **No MCP connection test**: The placeholder is deliberately disabled.

On each workstation, first check the installed version and syntax:

```sh
muse-code --version
jq -e . "${XDG_CONFIG_HOME:-$HOME/.config}/muse/settings.json"
```

Then start a fresh session, check `/effort`, `/theme`, and `/mcp`, and review startup warnings. Do not use `muse config validate --plane defaults --file settings.json` on this flat file: that command validates an enterprise document with a different envelope, as confirmed by the tested binary's help and described in the [configuration documentation](https://dev.meta.ai/docs/muse-code/configuration).

The hook command and optional launcher target POSIX environments, including your Arch setup and a compatible shell environment on other workstations. Native Windows shell compatibility and Termux execution were not tested; do not treat this as a verified native PowerShell configuration.

Distribute `settings.json` and, if used, `muse-local` through your dotfiles. Install dependencies and authenticate separately on each workstation; do not copy authentication files or workspace trust records as part of this template.
