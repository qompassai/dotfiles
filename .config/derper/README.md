# derper — companion notes for `derper.json`
Workstation: primo (Arch Linux) · generated 2026-09-28

Researched from upstream on 2026-09-28 (primary source — the daemon's own
flag definitions and config loader):
  https://github.com/tailscale/tailscale/blob/HEAD/cmd/derper/derper.go

## What `derper.json` is

`derper -c <path>` does **not** take daemon settings. It takes the path of a
JSON file holding the DERP node's private key:

```json
{ "PrivateKey": "<64 lowercase hex chars>" }
```

The file is created with mode `0600` by derper itself (`writeNewConfig`,
JSON pretty-printed with tab indent). Behavior:

- If the file is missing, derper **generates a fresh key and writes the
  file itself** on first run — this is the recommended way to create it.
- If you run as root and omit `-c`, derper defaults to
  `/var/lib/derper/derper.key`.
- If you run as non-root and omit `-c`, derper exits fatally
  (`-c <config path> not specified`).

The placeholder in `derper.json` is intentionally invalid: derper will fail
loudly at startup (`derper: config: ...`) until you replace it with a real
key. Delete the file and let derper generate one, or point `-c` at a path
where derper may write.

**Key handling rules:** this file is a long-term node identity. Never commit
a real key to a shared/dotfiles repo — keep the generated file out of git
(chmod 0600, owned by the derper user). If this repo is public, the
placeholder above is the correct committed state.

## Judgment call: no `flags.env` (SKIP)

`derper` is a flags-only daemon. Its only environment variable is
`TAILSCALE_DERPER_MESH_KEY`, read **in `-dev` mode only**. Upstream provides
**no** environment-file / `flags.env` mechanism, so inventing one would be a
made-up config format. There is no `flags.env` in this directory on purpose.
Pass the flags below on the command line or in your own systemd unit's
`ExecStart`.

## Every documented flag (from `derper.go`, 2026-09-28)

| Flag | Default | Notes |
| --- | --- | --- |
| `-a` | `:443` | HTTP/HTTPS listen addr (`:port`, `ip:port`, `[ip]:port`). HTTPS iff port is 443 and/or `-certmode=manual`, else HTTP. |
| `-http-port` | `80` | HTTP port on the same IP as `-a`; `-1` disables. |
| `-stun-port` | `3478` | UDP STUN port on the same IP as `-a`. |
| `-c` | `/var/lib/derper/derper.key` (root) | JSON private-key file; see above. |
| `-certmode` | `letsencrypt` | `manual` \| `letsencrypt` \| `gcp`. |
| `-certdir` | `tsweb.DefaultCertDir("derper-certs")` | ACME cert storage dir (only when `-a` is :443). |
| `-hostname` | `derp.tailscale.com` | TLS hostname for certs. May be an IP with `-certmode=manual` (skips SNI) or with `-acme-ip-certs`. |
| `-acme-eab-kid` | `""` | ACME External Account Binding key ID (required for `-certmode=gcp`). |
| `-acme-eab-key` | `""` | ACME EAB HMAC key, base64 (required for `-certmode=gcp`). |
| `-acme-email` | `""` | ACME account contact (required for gcp, optional for letsencrypt). |
| `-acme-ip-certs` | `false` | Serve short-lived (~6 day) Let's Encrypt certs for the server's own IPs via HTTP-01 on port 80. Requires `-certmode=letsencrypt`. |
| `-stun` | `true` | Run the STUN server. |
| `-derp` | `true` | Run the DERP server (set false only when decommissioning but keeping bootstrap DNS). |
| `-dev` | `false` | Localhost dev mode; overrides `-a` to `:3340`, uses an ephemeral key, reads mesh key from `TAILSCALE_DERPER_MESH_KEY`. |
| `-home` | `""` | Root-path content: default homepage, `"blank"` for empty, or a URL to redirect to. |
| `-mesh-psk-file` | `$HOME/keys/derp-mesh.key` | Mesh pre-shared key file; must be 64 lowercase hex chars (whitespace trimmed). |
| `-mesh-with` | `""` | Comma-separated hostnames to mesh with (own hostname may be listed; `host/dialname` form allowed). |
| `-secrets-url` | `""` | SETEC server URL for mesh-key retrieval (alternative to `-mesh-psk-file`). |
| `-secrets-path-prefix` | `prod/derp` | SETEC path prefix for the `meshkey` secret. |
| `-secrets-cache-dir` | `$HOME/.cache/derper-secrets` | SETEC secret cache dir (required if `-secrets-url` set). |
| `-bootstrap-dns-names` | `""` | Comma-separated hostnames served at `/bootstrap-dns`. |
| `-unpublished-bootstrap-dns-names` | `""` | Same, but not published in the list; `host/record` form polls a TXT record for rollout %. |
| `-verify-clients` | `false` | Verify clients via a local tailscaled instance. |
| `-verify-client-url` | `""` | Admission-controller URL for client connections (see `tailcfg.DERPAdmitClientRequest`). |
| `-verify-client-url-fail-open` | `true` | Fail open if the admission URL is unreachable. |
| `-disallow-app-names` | `""` | Comma-separated client-advertised app names to refuse (trusted mesh peers exempt). |
| `-socket` | `""` | Alternate tailscaled socket path (only with `-verify-clients`). |
| `-accept-connection-limit` | `+Inf` | Rate limit for accepting new connections. |
| `-accept-connection-burst` | `MaxInt` | Burst limit for accepting new connections. |
| `-rate-config` | `""` | Path to JSON rate-limit config (experimental, subject to change; reloaded on SIGHUP). |
| `-tcp-keepalive-time` | `10m` | TCP keepalive time (intentionally long; L7 keepalive runs more often). |
| `-tcp-user-timeout` | `15s` | TCP user timeout (intentionally short; DERPs should be near users). |
| `-tcp-write-timeout` | `derpserver.DefaultTCPWiteTimeout` | Write timeout for client TCP connections; `0` = no timeout. Not applied to mesh connections. |
| `-ace` | `false` | Embedded ACE server — experimental, in-development, undocumented as of 2025-09-12. |
| `-version` | — | Print version and exit. |

Default public surface: TCP 443 + TCP 80 + UDP 3478.

## Minimal systemd example (you own this; not upstream)

```ini
[Unit]
Description=Tailscale DERP server
After=network-online.target
Wants=network-online.target

[Service]
User=derper
ExecStart=/usr/local/bin/derper \
  -c /home/phaedrus/.config/derper/derper.json \
  -hostname derp.example.com \
  -a :443
Restart=on-failure

[Install]
WantedBy=multi-user.target
```
