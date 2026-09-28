# rpm — RPM package manager / build system (configuration reference)

## What this app is

RPM is the package manager and build system used by RPM-based Linux
distributions (Fedora, RHEL, openSUSE, ...). On Arch it is available from
the AUR as `rpm-tools-git` (upstream: <https://rpm.org/>,
source: <https://github.com/rpm-software-management/rpm>).

## Doc references (accessed 2026-09-28)

- RPM macro syntax and the rpmrc-to-macros migration:
  <http://ftp.rpm.org/api/4.4.2.2/macros.html>
- Fedora packaging guidelines, RPMMacros (key macro table):
  <https://docs.fedoraproject.org/en-US/packaging-guidelines/RPMMacros/>
- rpm(8), FILES section (config search paths):
  <https://manpages.opensuse.org/Leap-15.6/rpm/rpm.8.en.html>
- rpm-rpmrc(5), RPM 6.1.0 (directive list, search path, XDG behavior):
  <https://www.mankier.com/5/rpm-rpmrc>
- openSUSE packaging conventions ("/etc/rpm is for per-system
  adjustments"):
  <https://en.opensuse.org/openSUSE:Packaging_Conventions_RPM_Macros>
- Maximum RPM, "The rpmrc File" appendix (classic directive reference):
  <https://rikers.org/rpmbook/node122.html>

## User configuration mechanism

Two complementary files:

| File in this repo      | Real location            | Format / purpose                              |
|------------------------|--------------------------|-----------------------------------------------|
| `.config/rpm/macros`   | `/etc/rpm/macros`        | `%name value` lines: build dirs, install paths, flags, identity, signing |
| `.config/rpm/rpmrc`    | `~/.config/rpm/rpmrc`    | `VARIABLE: ARCH: VALUE` lines: arch/OS canon names, compat tables, per-arch optflags |

Notes:

- `macros` is the **system-level** template: rpm(8) reads
  `/usr/lib/rpm/macros`, `/usr/lib/rpm/<vendor>/macros`, `/etc/rpm/macros`,
  then `~/.rpmmacros`. Deploy this repo's copy to `/etc/rpm/macros`.
- `rpmrc` is stored at its **real per-user path**: RPM 6 reads
  `~/.config/rpm/rpmrc` (under `$XDG_CONFIG_HOME`), after the factory
  `/usr/lib/rpm/rpmrc`, vendor, and system `/etc/rpmrc` files.
- The canon numbers in `rpmrc` (e.g. `x86_64 … 11`) are historical and
  unused by rpm but must be present; values match upstream factory defaults.
- `%_gpg_name` in `macros` stays commented until you own a real GPG key.

## Validation

No RPM binary is installed in this environment, so both files are validated
structurally instead of with `rpm --showrc` / `rpm --eval`:

- `macros`: every active (non-comment, non-blank) line matches
  `%name value` (or the parameterized `%name(opts) body` form).
- `rpmrc`: every active line matches the rpm-rpmrc(5) synopsis
  `VARIABLE: ARCH: VALUE` / `VARIABLE: ARCH VALUE`, i.e. starts with a
  lowercase directive name followed by a colon, and the directive is one of
  the eight documented in rpm-rpmrc(5).
