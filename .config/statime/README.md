# statime — Pendulum PTP daemon (configuration reference)

## What this app is

`statime` is the Precision Time Protocol (PTP, IEEE 1588) daemon from the
Pendulum project, written in Rust. It keeps clocks synchronized across a
network at sub-microsecond precision: instances elect a grandmaster clock
via the best-master-clock algorithm and discipline the remaining clocks to
it. Upstream: <https://github.com/pendulum-project/statime>,
docs: <https://docs.statime.pendulum-project.org/>.

## Doc references (accessed 2026-09-28)

- statime.toml(5) man page (complete option list with defaults):
  <https://docs.statime.pendulum-project.org/man/statime.toml.5/>
- Getting-started guide:
  <https://github.com/pendulum-project/statime/blob/HEAD/docs/guide/getting-started.md>
- Man page sources:
  <https://github.com/pendulum-project/statime/blob/HEAD/docs/man/statime.toml.5.md>
  <https://github.com/pendulum-project/statime/blob/HEAD/docs/man/statime.8.md>
- Exporting metrics guide:
  <https://github.com/pendulum-project/statime/blob/HEAD/docs/guide/exporting-metrics.md>

## User configuration mechanism

One TOML file:

| File in this repo            | Real location              | Format / purpose                    |
|------------------------------|----------------------------|-------------------------------------|
| `.config/statime/statime.toml` | `/etc/statime/statime.toml` | TOML: clock identity/domain, `[[port]]` blocks (one per NIC), `[observability]` |

Sections and every documented option:

- Top level: `identity` (unset → derived from MAC), `domain` (0),
  `sdo-id` (0), `slave-only` (false), `priority1`/`priority2` (128),
  `path-trace` (bool, no documented default — set false here),
  `virtual-system-clock` (false).
- `[[port]]`: `interface` (required), `acceptable-master-list` (unset →
  accept all), `announce-interval` (1), `announce-receipt-timeout` (3),
  `delay-asymmetry` (0), `delay-interval` (0), `delay-mechanism` ("E2E"),
  `hardware-clock` ("auto" | "required" | "none" | index),
  `master-only` (false), `minor-ptp-version` (1), `sync-interval` (0).
  Intervals are exponents of 2 (1 = every 2s, 0 = every 1s).
- `[observability]`: `metrics-exporter-listen` ("127.0.0.1:9975"),
  `observation-path` (unset → no observation socket),
  `observation-permissions` (0o666 — always write with the `0o` prefix).

Judgment calls in the template (documented in the file header):

- `identity` and `acceptable-master-list` are commented out: fabricating
  values would claim a false clock identity or silently restrict which
  masters are followed.
- `interface = "lo"` is the man page's own placeholder; point it at a real
  PTP-capable NIC on a real deployment.
- `observation-path` is set explicitly (unlike the default) so
  `statime-metrics-exporter` can actually observe the daemon.

## Validation

Parsed with Python `tomllib` (real TOML parser): all tables, keys, and the
`0o666` octal literal load successfully.
