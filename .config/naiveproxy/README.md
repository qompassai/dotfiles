# naiveproxy — companion notes for `config.json`
Workstation: primo (Arch Linux) · generated 2026-09-28

Researched from upstream on 2026-09-28:
  https://github.com/klzgrad/naiveproxy/blob/HEAD/README.md
  https://github.com/klzgrad/naiveproxy/blob/master/USAGE.txt
  (full option reference; config-file semantics)

`config.json` is strict JSON and cannot contain comments, so everything
that would be a comment lives here. Keys are alphabetically ordered in
the file.

## How the file is used

`naive [/path/to/config.json]` — defaults to `./config.json` in the
working directory. Every `--flag=value` also works as a `"flag": value`
JSON key; **a flag given N times on the command line equals a JSON array
of N strings** (so `listen`, `extra-headers`, and `host-resolver-rules`
accept a string or an array of strings).

## Every documented option (values in `config.json`)

- `listen` = `"socks://127.0.0.1:1080"` — ELI5: where your apps connect
  to naive locally. Format: `<proto>://[user:pass@][addr][:port]`,
  proto is `socks` | `http` | `redir`. Documented defaults are
  `socks`, `0.0.0.0`, `1080`; this file binds loopback only on purpose.
  `redir` needs iptables REDIRECT rules, carries no authentication, and
  also enables a DNS resolver on the same UDP port (the resolver answers
  with artificial addresses from `resolver-range` that are translated
  back to domain names in the proxy request and resolved remotely —
  note downstream caches can go stale).
- `proxy` = `"https://user:REPLACE-ME@proxy.example.com:443"` — ELI5:
  the upstream server your traffic is tunneled through. Format:
  `<http|https|quic>://[user:pass@]host[:port]` chains (comma-separated)
  or `socks://host[:port]` (no chaining/auth/padding). The last hop
  negotiates Naive padding automatically; QUIC cannot follow TCP proxies
  in a chain; you must avoid loops. **REPLACE-ME before use**
  (`proxy.example.com` is RFC 2606 reserved and never resolves, so the
  placeholder fails closed). Omitting `proxy` entirely means direct
  connection with no proxying.
- `insecure-concurrency` = `1` — ELI5: how many parallel tunnel
  connections to keep. More survives bad networks but makes traffic
  easier to fingerprint; upstream "strongly recommends against" more
  than 4. `1` is the strongest setting.
- `tunnel-timeout` = `1800` — ELI5: after this many seconds a tunnel
  connection is retired (new streams move to fresh connections; old
  streams are closed by the idle or tunnel timeout). Helps on CGNAT
  networks with stuck long-lived connections, but breaks long-lived TCP
  protocols like SSH. Documented default: 1800 (600 on Android).
- `idle-timeout` = `600` — ELI5: streams idle this long are forcibly
  closed so retired connections get cleaned up. Documented default: 600
  (300 on Android).
- `resolver-range` = `"100.64.0.0/10"` — ELI5: the CGN address pool the
  built-in redir DNS resolver hands out as artificial addresses.
  Documented default.
- `extra-headers` = `[]` — ELI5: extra HTTP headers added to upstream
  proxy requests. Repeatable flag → string or array of strings.
- `host-resolver-rules` = `[]` — ELI5: static DNS overrides, e.g.
  `"MAP proxy.example.com 1.2.3.4"`. Repeatable flag → string or array.
- `log` = `""` — ELI5: where naive writes its log. Three states:
  **absent** = no log saved or printed (the privacy default);
  **empty string** = print to console (this file's setting);
  **a path** = write to that file.
- `no-post-quantum` = `false` — ELI5: post-quantum key agreement stays
  ON (`false` = do not disable). Set `true` only to work around a broken
  middlebox.

## Deliberately omitted (judgment call)

- `log-net-log` (`--log-net-log=<path>`) and `ssl-key-log-file`
  (`--ssl-key-log-file=<path>`) — both are opt-in debug features with a
  **required** path argument and no documented "disabled" value; an
  empty or guessed value could create files or error out, and the SSL
  key log in particular would expose session secrets for Wireshark.
  Omitting them is the documented off state (nothing is recorded).
  NetLog can be inspected at https://netlog-viewer.appspot.com/ when you
  do enable it.
- `-h`/`--help`/`--version` are CLI-only, not config options.

## Validation

`python3 -m json.tool config.json` — strict JSON parse (2026-09-28: OK).
No `naive` binary exists on this machine, so the native config parser
could not be run; JSON validity plus USAGE.txt-conformant key names and
types is the verified state.
