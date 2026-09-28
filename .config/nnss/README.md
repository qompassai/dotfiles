# nnss — Network Namespace setup using SSH SOCKS proxy — SKIP

## Verdict: SKIP — no verified config-file mechanism exists

`nnss` (AUR `nnss` 0.4.0-2, MPL-2.0, depends on `tun2socks`) sets up a
network namespace routed through an SSH SOCKS proxy. Its AUR packaging
does exactly one thing:

```sh
make PREFIX="$pkgdir/usr" install
```

No configuration file is installed — not to `/etc`, not to
`~/.config`, nowhere. There is no documented config file, config
directory, or environment-file mechanism in the packaging, and no
config format could be verified from any reachable primary source.

## Research trail (accessed 2026-09-28)

- AUR package page: <https://aur.archlinux.org/packages/nnss>
  (pkgdesc: "Network Namespace setup using SSH SOCKS proxy")
- AUR git (PKGBUILD quoted above): <https://aur.archlinux.org/nnss.git>
- Upstream repo: <https://gitea.balki.me/balki/nnss> — **unreachable**:
  HTTP fetch returned an empty HTTP 500 after retries, `git clone`
  failed with TLS termination, and the AUR web page later hit Anubis
  denial. Per task instructions this upstream was not retried further
  (no changed arguments, no alternate endpoints).

## Why not invent one

nnss is driven by command-line invocation (namespace name, SSH target,
proxy port), not by a config file. Writing a speculative
`~/.config/nnss/...` file would invent a mechanism the software does not
read. If upstream later documents one, this verdict should be revisited
against the live source.

## Validation

N/A — no files generated. This README exists only to record the verdict
so the batch audit can account for the app.
