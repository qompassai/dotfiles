# Changelog

## 2026-09-28 — Exhaustive configs for 18 apps missing from dotfiles

Source: the 2026-09-27 inventory of `/etc` directories on primo with no
dotfiles twin (`etc-dirs-no-dotfile-twin.txt`, 22 entries). 18 gained
configs; 4 were deliberately skipped (see "Skips" below).

Conventions for every new config (Matt's directive):
- EVERY documented option explicitly set, even when it equals the default.
- Options in alphabetical order as far as the format allows.
- Header comment block with the official documentation links actually
  fetched on 2026-09-28 (no training-memory URLs).
- Section comments + ELI5 one-liners for non-obvious options.
- Safe-by-default values: loopback binds, authentication on, no real
  secrets or keys committed (placeholders where a secret belongs).

Validation: 37 new files. Every file parsed with a real parser —
`tomllib`, `pyyaml`, `json.tool`, `configparser`, `python-hcl2`, a
hand-written KDL v1 grammar parser, plus app-specific structural checks
(minetest.conf grammar reimplementation, TouchHLE options parser
extracted verbatim from upstream Rust source, oslo.config end-to-end
for tempest, JVM-flags and dotenv structural checks). 37/37 pass.
Native semantic validation (running each binary) was unavailable in
this environment; each file's header says so where applicable.

### Added

- **aperture-router** — `.config/aperture-router/config.toml`
  LLM-gateway router (wayazi/aperture-router). Secure defaults: loopback
  bind, localhost upstream, empty key arrays, `require_auth_in_prod=true`.
  `api_key` deliberately omitted — provisioned via `APERTURE_API_KEY` env
  var, never committed. Fully-worked `[[providers]]` example commented out.
  Docs: github.com/wayazi/aperture-router `docs/reference/configuration.md`.
- **databend** — `.config/databend/databend-query.toml`,
  `.config/databend/databend-meta.toml`
  Cloud data warehouse. Mirrors the current main-branch distribution
  templates; all 8 storage backends (azblob, cos, fs, gcs, hdfs, oss, s3,
  webhdfs) present as placeholders with `fs` active. Legacy `storage.obs`
  (renamed `oss` upstream) and legacy `log.file.on`/`log.stderr.*`
  toggles omitted — absent from the current template. Newer
  changelog-mentioned query options
  (aggregate/join_spilling_memory_ratio, max_running_queries,
  data_retention_time_in_days_max) omitted as unverifiable (official
  config page fetch timed out, not retried — not invented).
  Docs: databendlabs/databend `scripts/distribution/configs/`, docs.databend.com.
- **derper** — `.config/derper/derper.json`, `.config/derper/README.md`
  Tailscale DERP relay. derper is flags-only upstream (no env-file
  mechanism); `derper.json` carries a `REPLACE-WITH-GENERATED-KEY`
  placeholder (derper generates the real key on first run — committing a
  real key would be wrong). All 30+ documented flags tabulated in the
  README with a minimal systemd example.
  Docs: tailscale/tailscale `cmd/derper/derper.go`.
- **elasticsearch** — `.config/elasticsearch/elasticsearch.yml`,
  `.config/elasticsearch/jvm.options`
  90 top-level YAML keys: cluster/node identity, paths, network
  (transport/http incl. CORS), discovery/cluster formation (single-node
  dev default; multi-node path documented), gateway, indices
  caches/circuit breakers, monitoring, xpack security TLS as written by
  first-boot auto-configuration. Dynamic-only deep xpack features
  (watcher/ILM/CCR/ML internals) and per-index settings excluded as
  runtime/API concerns. jvm.options: heap, G1GC, heap-dump, GC log
  rotation, tmpdir; header notes upstream's "don't edit root
  jvm.options, use jvm.options.d/" guidance.
  Docs: elastic.co configuration reference, jvm-settings, important-settings.
- **iocaine** — `.config/iocaine/config.kdl`
  Techaro "iocaine" AI-scraper tarpit (KDL v1). Single-file mode with
  handler + servers declared explicitly. `unwanted-asns.db-path`
  commented out (missing GeoIP DB fails handler init). Top-level
  `firewall.enable=false` (needs root/nftables). Validated with a
  hand-written KDL v1 grammar parser cross-checked against upstream's
  own corpus — npm/PyPI KDL libraries are v2 or broken and were rejected.
  Docs: git.madhouse-project.org/iocaine/iocaine @ iocaine-3.5.0.
- **luanti** — `.config/luanti/minetest.conf`
  Luanti (formerly Minetest) voxel game. **586 settings**, generated
  programmatically from upstream's current `minetest.conf.example`
  (2026-09-28) — not hand-transcribed. Alphabetized within 24 sections,
  upstream descriptions + `# type:` lines preserved. Noise-param groups
  converted to the parser-valid single-line form (verified behaviorally
  identical in `src/noise.cpp`/`src/settings.cpp`). `secure.*` settings
  excluded (stripped by `Settings::removeSecureSettings`, never take
  effect). `default_password` shown empty (upstream redacts it in the
  example; true default verified in `src/defaultsettings.cpp`).
  Docs: github.com/luanti-org/luanti `minetest.conf.example`.
- **makeuki** — `.config/makeuki/makeuki.conf`, `.config/makeuki/README.md`
  Unified-kernel-image builder (AUR). 9/9 keys, alphabetical,
  `secure_boot=false`. `command_line` uses a real-shaped but visibly
  incomplete `root=UUID=PASTE-YOUR-ROOT-FS-UUID-HERE` placeholder
  replacing the AUR package's nonsense default.
  Docs: aur.archlinux.org `makeuki` (only verified authority; no upstream docs found).
- **naiveproxy** — `.config/naiveproxy/config.json`, `.config/naiveproxy/README.md`
  Chromium-stack forward proxy. Strict JSON (comments live in README).
  Loopback SOCKS listener, `insecure-concurrency=1`, PQ key agreement on.
  `proxy` placeholder uses `proxy.example.com` (RFC 2606, fails closed).
  `log-net-log`/`ssl-key-log-file` deliberately omitted — opt-in debug
  features with no documented "off" value; omitting is the safe default.
  Docs: github.com/klzgrad/naiveproxy README + USAGE.txt.
- **network** — `.config/network/ifupdown-ng.conf`, `interfaces`,
  `ifupdown-ng.default`, `README.md`
  Judgment call: "network" was ambiguous, but ifupdown-ng is the only
  package owning `/etc/network/` on Arch (ADMIN-GUIDE documents
  `/etc/network/interfaces` + `ifupdown-ng.conf`; AUR PKGBUILD installs
  `/etc/default/ifupdown-ng`). 7/7 documented booleans at defaults
  (behavior-neutral); `interfaces` has loopback live, guide's own
  DHCP/IPv6-RA/static/GRE examples commented out.
  Docs: github.com/ifupdown-ng/ifupdown-ng `doc/ADMIN-GUIDE.md`.
- **odysseus-ai** — `.config/odysseus-ai/odysseus.env`, `README.md`
  dotenv, 78 active lines / 78 unique keys / 0 malformed. All 49 AUR
  `.env.example` vars plus source-level settings. Secure:
  `AUTH_ENABLED=true`, `LOCALHOST_BYPASS=false`, loopback bind. Documents
  the pinned source default `ODYSSEUS_BROWSER_NO_SANDBOX=1` (sandbox is
  disabled unless explicitly set to 0/false/no).
  Docs: github.com/odysseus-dev/odysseus `website/setup.md`, AUR page.
- **openbao** — `.config/openbao/openbao.hcl`
  OpenBao (Vault fork) server. Single-node Raft + TLS-1.3-only loopback
  listener; `disable_clustering=false` (mandatory with Raft);
  `ha_storage` absent (forbidden with Raft); Shamir seal (no `seal`
  stanza = manual unseal, documented). `tls_key_exchange_preferences` =
  docs' enforce-PQC hybrid set. Unauthenticated
  metrics/pprof/rekey/generate-root endpoints disabled. File audit with
  `log_raw=false`, `hmac_accessor=true`. Two corrections during
  validation: `disable_mlock` omitted (not in the official reference —
  would be invented); docs' `custom_response_headers { "default" = {} }`
  uses quoted attribute names which are **invalid HCL** — dropped with a
  comment noting the discrepancy.
  Docs: github.com/openbao/openbao `website/content/docs/configuration/`.
- **repkg** — `.config/repkg/rules/example-pkg.rule`,
  `.config/repkg/rules/ruby-*.rule`,
  `.config/repkg/rules/+example-pkg.rule`, `.config/repkg/README.md`
  Skycoder42 repkg (pacman hook dependency tracker): one
  `<package>.rule` per package, single line of space-separated deps with
  `=<filter>` suffixes; all 8 version-filter forms demonstrated.
  Inert by construction (example packages don't exist as targets).
  Upstream is archived/discontinued since 2019 (AUR deletion requested
  2023) — template of the documented mechanism only.
  Docs: github.com/Skycoder42/repkg.
- **rpm** — `.config/rpm/macros`, `.config/rpm/rpmrc`, `README.md`
  RPM package manager. `macros`: 38 active lines (system template for
  `/etc/rpm/macros`); `rpmrc`: 13 active lines, all 8 documented
  directives (canonical at `~/.config/rpm/rpmrc` in RPM 6+).
  `%_gpg_name` intentionally commented — a fake key ID would break
  signed builds.
  Docs: rpm.org macros API, Fedora packaging guidelines, rpm/rpmrc man pages.
- **statime** — `.config/statime/statime.toml`, `README.md`
  Statime Rust PTP daemon (Pendulum). `[[port]]` 10/10 options
  alphabetical (identity and acceptable-master-list intentionally unset);
  `[observability]` 3/3; `observation-permissions = 0o666`. Safe template:
  `interface="lo"`, `hardware-clock="auto"`, `path-trace=false`.
  Docs: docs.statime.pendulum-project.org `man/statime.toml.5/`.
- **tempest** — `.config/tempest/tempest.conf`, `accounts.yaml`,
  `allow-list.yaml`, `logging.conf`, `rbac-persona-accounts.yaml`,
  `README.md`
  OpenStack Tempest test runner. `tempest.conf`: 23 sections + DEFAULT,
  validated **end-to-end with real oslo.config** (`register_opts()` +
  parse): 192 checkable options, 190 match documented defaults exactly;
  the 2 diffs are proven serializer/parser artifacts (documented in
  README). 34 `<None>` defaults left commented (`<None>` = unset
  placeholder, not a value). The other four files are byte-identical to
  upstream 28.0.0 `etc/` samples (verified by diff); passwords are
  upstream `'test_password'` placeholders only.
  Docs: github.com/openstack/tempest, docs.openstack.org/tempest.
- **touchhle** — `.config/touchhle/touchHLE_options.txt`
  TouchHLE iOS emulator options file. Comment-only template mirroring
  upstream's own 15-line template style (no fabricated bundle IDs or
  mapping coordinates). All 30 file-usable options documented with
  genuine bundle IDs from upstream's `touchHLE_default_options.txt`.
  Validated with a tiny Rust crate embedding upstream's verbatim
  `get_options_from_file` (5/5 checks pass).
  Docs: github.com/touchHLE/touchHLE `src/options.rs`, `OPTIONS_HELP.txt`.
- **v4l2-relayd.d** — `.config/v4l2-relayd.d/virtual-camera.conf`, `README.md`
  v4l2-relay drop-in (verified in upstream 0.2.0 source: generator
  enumerates `/etc/v4l2-relayd.d/*.conf`; `v4l2-relayd@.service` sources
  `/etc/default/v4l2-relayd` then `/etc/v4l2-relayd.d/%i.conf`). 8/8
  documented vars, alphabetical (CARD_LABEL, EXTRA_OPTS, FORMAT,
  FRAMERATE, HEIGHT, SPLASHSRC, VIDEOSRC, WIDTH).
  Docs: gitlab.com/vicamo/v4l2-relayd, AUR page.
- **nnss** — `.config/nnss/README.md` (verdict only; see Skips)

### Skips (deliberate, no config invented)

- **gnucash** — GnuCash stores preferences in GSettings via the dconf
  database (`~/.config/dconf/user`); there is no portable per-app text
  config file (verified: wiki.gnucash.org/wiki/Configuration_Locations).
- **eac** — `/etc/eac` is OpenSC's packaged EAC/PACE certificate material
  (`/etc/eac/cvc/...`), not an application config directory. Nothing to configure.
- **RTL** — no distinct package owns `/etc/RTL`; the existing
  `.config/rtl_433/` (SDR tool) is a different thing and already covered.
- **shairplay** — CLI-flags-only AirPlay server; no config-file parser
  exists upstream. Not inventing one.
- **nnss** — AUR `nnss` 0.4.0-2 ("Network Namespace setup using SSH SOCKS
  proxy") installs binaries with zero config files and no documented
  config mechanism (upstream Gitea unreachable: HTTP 500). README records
  the verdict.

### Notes

- Additive-only: 18 new directories under `.config/` (+ CHANGELOG.md).
  No existing file modified. `nvim`, `hypr`, and all other existing
  configs untouched.
- No real secrets committed anywhere (placeholders only).
- Display quirk (batch C): tool output rendering redacts password-like
  lines — byte-level inspection proved `default_password` is truly empty
  in `minetest.conf`; the file is correct.
