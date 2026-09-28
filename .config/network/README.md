# network — interface configuration (`/etc/network`, ifupdown-ng)

## What this app is

On Arch, `/etc/network` is not native networking configuration (native
Arch uses systemd-networkd `/etc/systemd/network`, netctl, or
NetworkManager). It is the Debian/Alpine-style interface database owned
by the AUR package **`ifupdown-ng`**: a network device manager backwards
compatible with traditional `ifup`/`ifdown`, with a dependency-solver for
interface bring-up order. These files template its three config surfaces.

## Doc references (accessed 2026-09-28)

- Admin guide (filesystem paths, `ifupdown-ng.conf` settings, `interfaces`
  stanza syntax and examples):
  <https://github.com/ifupdown-ng/ifupdown-ng/blob/main/doc/ADMIN-GUIDE.md>
- `dist/ifupdown-ng.conf.example` (all seven settings, documented defaults):
  <https://github.com/ifupdown-ng/ifupdown-ng/blob/main/dist/ifupdown-ng.conf.example>
- Service defaults + kill-switch handling:
  <https://github.com/ifupdown-ng/ifupdown-ng/blob/main/dist/debian/networking.default>
  and `dist/debian/networking`
- AUR packaging (installs `/etc/default/ifupdown-ng`, the systemd unit,
  and the `networking` wrapper):
  <https://aur.archlinux.org/packages/ifupdown-ng>

## Configuration mechanism: three files

| File in this repo | Real location | Purpose |
|---|---|---|
| `.config/network/ifupdown-ng.conf` | `/etc/network/ifupdown-ng.conf` | Global behaviour: 7 boolean settings, all explicitly set to documented defaults |
| `.config/network/interfaces` | `/etc/network/interfaces` | Interface database: `auto`/`iface` stanzas, `use` executor selection |
| `.config/network/ifupdown-ng.default` | `/etc/default/ifupdown-ng` | Shell-sourced service defaults (`CONFIGURE_INTERFACES`, `VERBOSE`, `SKIP_DOWN_AT_SYSRESET`) |

Judgment calls:

- `ifupdown-ng.conf` is optional upstream (absent == all defaults); this
  template spells all 7 settings out explicitly and is behaviour-neutral.
- `interfaces` keeps only the loopback stanza live; the `eth0` DHCP /
  IPv6-RA / static / GRE examples are the admin guide's own, commented
  out — interface names and addresses must be adapted per machine.
- Executor-specific stanza options (bond, bridge, vlan, …) are documented
  in `interfaces(5)` / `ifupdown-executor(7)` and intentionally not
  enumerated here.

## Validation

- `ifupdown-ng.conf`: 7/7 documented settings present, `key = value`
  syntax matches upstream's example file, alphabetically ordered.
- `interfaces`: stanza syntax (`auto`, `iface`, `use`, `requires`,
  `address`, `gateway`, `gre-*`) matches the admin guide examples.
- `ifupdown-ng.default`: valid shell assignments (`bash -n` clean),
  variable names match `dist/debian/networking.default`.
