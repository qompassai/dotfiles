# odysseus-ai — local-first AI workspace (configuration reference)

## What this app is

Odysseus is a local-first AI workspace: chat with LLMs, RAG over your
documents, email, calendar, gallery, and scheduled automations, served as a
web UI by uvicorn. Upstream: <https://github.com/odysseus-dev/odysseus>;
AUR package: `odysseus-ai`.

## Doc references (accessed 2026-09-28)

- Upstream repository: <https://github.com/odysseus-dev/odysseus>
- Setup guide: <https://github.com/odysseus-dev/odysseus/blob/dev/website/setup.md>
- AUR package page: <https://aur.archlinux.org/packages/odysseus-ai>
- AUR-pinned source, commit `cf4e240ad1622da6a904f496b19d656a2b9c6393`
  (`.env.example`, `setup.py`, `src/`, service units):
  <https://github.com/pewdiepie-archdaemon/odysseus>

## User configuration mechanism

One dotenv file:

| File in this repo                     | Real location                          |
|---------------------------------------|----------------------------------------|
| `.config/odysseus-ai/odysseus.env`     | `~/.config/odysseus-ai/odysseus.env` (user service) |
|                                       | `/etc/odysseus-ai/odysseus.env` (system service)    |

The AUR package installs `.env.example` as `/etc/odysseus-ai/odysseus.env`;
the user service unit reads `EnvironmentFile=-%h/.config/odysseus-ai/odysseus.env`,
and the AUR launcher wrapper (`/usr/bin/odysseus-ai`) honors
`ODYSSEUS_HOST` (default `127.0.0.1`) / `ODYSSEUS_PORT` (default `7000`).

The file sets **78 variables**: every variable from the AUR-pinned
`.env.example` (now explicit, including commented-out ones carrying their
documented defaults), the two AUR wrapper variables, `ODYSSEUS_ADMIN_USER`
and `OAUTH_REDIRECT_BASE_URL` (verified in `setup.py` / `src/mcp_oauth.py`),
plus an "Advanced tuning" set whose defaults were read from the pinned
source (each annotated with its `file:line`). Demo-script-only variables
(`DEMO_IMAP_*`, `DEMO_ALLOW_WIPE`) are intentionally omitted.

Security-relevant defaults worth knowing:

- `AUTH_ENABLED=true`, `LOCALHOST_BYPASS=false`, `APP_BIND=127.0.0.1`
  (loopback-only; the example's recommended posture).
- `SECURE_COOKIES=false` — set `true` only behind trusted HTTPS.
- `ODYSSEUS_BROWSER_NO_SANDBOX=1` is the code default: the MCP helper
  browser runs **without** Chromium's sandbox unless you set `0/false/no`.
- `ODYSSEUS_ENABLE_HOST_DOCKER` alone does nothing; it must be paired
  with the `docker/host-docker.yml` compose overlay (raw socket access).
- All secrets are empty here by design — fill them in on the machine,
  never commit real keys.

## Validation

Dotenv has no single standard parser, so the file is validated
structurally: every active line matches `^[A-Za-z_][A-Za-z0-9_]*=.*$`
(no spaces around `=`, valid shell/env identifier), there are no duplicate
keys, and the variable set is cross-checked against the AUR-pinned
`.env.example` (every example variable present).
