# repkg — AUR rebuild tracker (user configuration reference)

**Status: UPSTREAM ARCHIVED / DISCONTINUED.** The repkg GitHub repository
(<https://github.com/Skycoder42/repkg>) is archived; the AUR package was
requested for deletion in 2023 as discontinued since 2019. This directory
documents the user-config mechanism as a template only.

## What this app is

`repkg` tracked which installed AUR packages needed rebuilding when one of
their dependencies was upgraded (e.g. a library soname bump). Pacman hooks
fired on every upgrade, and repkg rebuilt the affected AUR packages.

## Doc references (accessed 2026-09-28)

- Upstream repository and README (rule format, commands, version filters):
  <https://github.com/Skycoder42/repkg>
- Release notes showing the rule-format features:
  <https://github.com/Skycoder42/repkg/releases/tag/1.2.0>
  <https://github.com/Skycoder42/repkg/releases/tag/1.4.0>
- AUR deletion request (evidence of discontinuation since 2019):
  <https://lists.archlinux.org/archives/list/aur-requests@lists.archlinux.org/message/3JU7VRXUDWFHBEZQ4UATKN6BGSUWBBW2/>

## User configuration mechanism

There is **no global options file**. User configuration = rule files in:

```
~/.config/repkg/rules/
```

- One file per package: `<package>.rule`
- File content: a single line of **space-separated dependency names**.
  When any listed dependency is upgraded, `<package>` is rebuilt.
- **User rules override system rules** (`/usr/share/repkg/rules/`) for the
  same package.
- **Wildcard rules**: a file named e.g. `ruby-*.rule` applies to every
  package whose name matches the glob.
- **Extension rules**: a file named `+<rule>.rule` (e.g. `+ruby-gems.rule`)
  EXTENDS the matching wildcard rule instead of overriding it.

### Version filters

Each dependency may carry a `=<filter>` suffix controlling which upgrades
trigger a rebuild (suffixes combine, e.g. `foo=:1:2:s`):

| Filter | Meaning |
| ------ | ------- |
| (none) | any upgrade of the dependency triggers a rebuild |
| `v`    | only upgrades where the version *string* actually changed |
| `0`    | never trigger on this dependency |
| `<n>` (positive int) | only version-segment `<n>` changes trigger (1=major, 2=minor, ...) |
| `:<from>[:<to>]` | version-segment *range* that triggers (empty side = open end) |
| `s`    | trigger only when the shared-library (.so) files change |
| `r`    | trigger when the dependency is *removed* |
| `:<substring>` | trigger when the version string *contains* the substring |

Examples from the documented format:

```
my-pkg.rule        ->  dep-a dep-b=v dep-c=1 dep-d=0 dep-e=s dep-f=r dep-g=:2:4 dep-h=:1::v
ruby-*.rule        ->  ruby
+ruby-gems.rule    ->  rubygems=v
```

## Commands

- `repkg create <rule> [dep...]` — create a rule file from the CLI
- `repkg remove <rule>` — delete a rule file
- `repkg list [detail]` — list configured rules (detail = show deps)
- `repkg frontend [--set key=value ...]` — pick the AUR frontend
  (default `trizen`; also `yaourt`, `pacaur`, `yay`, `pikaur`), each with
  frontend-specific options settable via `--set`

## Files in this directory

- `rules/example-pkg.rule` — inert example exercising every documented
  version-filter form (package `example-pkg` does not exist, so nothing
  can ever trigger on it).
- `rules/ruby-*.rule` — inert example of a wildcard rule.
- `rules/+example-pkg.rule` — inert example of an extension rule.
