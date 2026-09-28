# makeuki — unified kernel image builder (configuration reference)

> JSON has no comments, so the documentation lives here. Every key below is
> read from `makeuki.conf` by `makeuki.sh` via `jq`.

## What this app is

`makeuki` ("make UKI") is a script that simplifies creating **unified kernel
images** (UKIs): a single EFI binary bundling the kernel, initramfs, kernel
command line, and splash image, built with `objcopy` around
`/usr/lib/systemd/boot/efi/linuxx64.efi.stub`. Optionally signs the result
for Secure Boot with `sbsign`. The AUR package ships
`/etc/makeuki/makeuki.conf.default` and its install script copies it to
`/etc/makeuki/makeuki.conf` on first install; the script reads exactly that
path (`CONFIG="/etc/makeuki/makeuki.conf"`). In this dotfiles repo the file
is stored as `.config/makeuki/makeuki.conf`.

## Doc references (accessed 2026-09-28)

- AUR package metadata (description, upstream URL field is empty):
  <https://aur.archlinux.org/rpc/v5/info/makeuki>
- AUR package git repository (PKGBUILD, `makeuki.install`, `makeuki.sh`,
  `makeuki.conf.default` — the authoritative source; no separate upstream
  project page or documentation was found):
  <https://aur.archlinux.org/makeuki.git>

## Notes / unverifiable details

- No upstream documentation exists beyond the AUR packaging; every behavior
  below was verified against `makeuki.sh` from the AUR tarball.
- The shipped `makeuki.conf.default` contains the literal placeholder
  `["insert", "command", "line", "parameters", "here"]` for
  `command_line`. This template replaces it with a real-shaped example;
  you **must** set your actual root filesystem (see below).
- `comment` is inert metadata — the script never reads it.

## Options (all keys, alphabetical)

ELI5: this file is the recipe card for baking one EFI file. It says which
kernel package to use, what boot instructions to bake in, where the oven
(workdir) is, where the finished dish goes (output_file), which picture to
print on top (splash), and whether to stamp it with a Secure Boot wax seal.

| Key              | Type         | Used as / ELI5                                              |
|------------------|--------------|-------------------------------------------------------------|
| `command_line`   | array of strings | Kernel boot parameters, joined with spaces into `cmdline.txt` and baked into the UKI as `.cmdline`. **Replace the placeholder**: find your root UUID with `findmnt -no UUID /` or `blkid`, then e.g. `["root=UUID=<uuid>", "rw", "quiet"]`. |
| `comment`        | string       | Inert note to self. Kept verbatim from the shipped default. |
| `kernel`         | string       | Pacman package name providing the kernel (`pacman -Ql <kernel>` must list a kernel image). Default `linux`; use `linux-lts`, `linux-zen`, etc. to match your installed kernel. |
| `output_file`    | string (path) | Where the finished UKI is copied. Must live on your ESP (the FAT partition your firmware boots), e.g. `/boot/linux.efi` or `/efi/EFI/Linux/arch.efi`. |
| `sb_cert_key`    | string (path) | Secure Boot signing certificate (`.crt`). Only used when `secure_boot` is true. |
| `sb_private_key` | string (path) | Secure Boot private key (`.key`) for `sbsign`. Only used when `secure_boot` is true. |
| `secure_boot`    | boolean      | `true` → sign the UKI with `sbsign --key <sb_private_key> --cert <sb_cert_key>` after building. `false` → skip signing (keys ignored). |
| `splash`         | string (path) | BMP image baked into the UKI as the `.splash` section (`--change-section-vma .splash=0x40000`). **The file must exist** — `objcopy --add-section` fails otherwise. |
| `workdir`        | string (path) | Scratch directory; the script `mkdir -p`s it and builds everything inside. |

## Validation

Parsed with `python3 -m json.tool` (real JSON parser) and structurally
checked: all 9 keys present, `command_line` is an array of strings (the
shape `jq 'command_line|join(" ")'` requires), `secure_boot` is a boolean.
