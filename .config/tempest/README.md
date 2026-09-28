# tempest — OpenStack integration test suite (configuration reference)

## What this app is

`tempest` is the OpenStack integration test suite: thousands of API tests
executed against a live OpenStack cloud. (The AUR package is
`openstack-tempest`; upstream: <https://github.com/openstack/tempest>.)

## Doc references (accessed 2026-09-28)

- Upstream source (28.0.0 tarball; `etc/` samples, `tools/check_logs.py`,
  `tempest/config.py` option definitions):
  <https://github.com/openstack/tempest>
- AUR package (installs all five files to `/etc/tempest`, runs
  `oslo-config-generator` to build `tempest.conf` from
  `tempest/cmd/config-generator.tempest.conf`):
  <https://aur.archlinux.org/packages/openstack-tempest>
- Tempest configuration guide:
  <https://docs.openstack.org/tempest/latest/configuration.html>
- Sample config reference:
  <https://docs.openstack.org/tempest/latest/sampleconf.html>

## Configuration mechanism: five files

| File in this repo | Real location | Format / purpose |
|---|---|---|
| `.config/tempest/tempest.conf` | `/etc/tempest/tempest.conf` | INI (oslo.config): auth, endpoints, feature flags, timeouts — 24 sections, 253 options |
| `.config/tempest/accounts.yaml` | `/etc/tempest/accounts.yaml` | YAML list of pre-provisioned test accounts (username/tenant/password/roles) |
| `.config/tempest/allow-list.yaml` | `/etc/tempest/allow-list.yaml` | YAML mapping for `tools/check_logs.py`: known-acceptable log errors (upstream ships it **empty**) |
| `.config/tempest/logging.conf` | `/etc/tempest/logging.conf` | Python `logging` fileConfig: loggers/handlers/formatters |
| `.config/tempest/rbac-persona-accounts.yaml` | `/etc/tempest/rbac-persona-accounts.yaml` | YAML list of RBAC persona accounts (system/domain/project × admin/member/reader) |

How `tempest.conf` was produced: ran `oslo-config-generator` against the
28.0.0 source (same as the AUR packaging), then uncommented every option
to its documented default while keeping the generator's explanatory
comments:

- 219 options uncommented (incl. 13 with genuinely empty defaults —
  `region =`, `tempest_roles =`, …).
- 34 options with `<None>` defaults **left commented**: `<None>` is the
  sample-file placeholder for "unset", not a settable value.
- The other four files are faithful copies of the upstream `etc/` samples
  (passwords are the upstream `'test_password'` placeholders).

Judgment calls (also in the file headers):

- Values that must be site-specific (auth URL, credentials, network IDs,
  image refs) are noted as requiring replacement before any real run.
- `provider_net_base_segmentation_id = 3000`: the generator emits `3000`
  (int→string warning is the generator's own); oslo.config coerces it at
  typed access, exactly as the AUR-built file behaves.
- `ssh_shell_prologue` keeps the generator's `$$PATH` escaping, which
  oslo.config unescapes to `$PATH` on read — the intended default.

## Validation

- `tempest.conf`: parses with `configparser` (interpolation off);
  **end-to-end with the real `oslo.config` parser** (`register_opts()` +
  parse): 192 checkable options, 190 match documented defaults exactly,
  2 differ only by the documented `$$` escaping / int coercion above.
- `accounts.yaml`, `rbac-persona-accounts.yaml`, `allow-list.yaml`:
  `yaml.safe_load` (allow-list loads as `None` — correct, it is empty).
- `logging.conf`: `configparser`.
