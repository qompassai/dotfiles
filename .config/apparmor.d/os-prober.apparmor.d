# apparmor.d - Full set of apparmor profiles
# Copyright (C) 2022-2024 Alexandre Pujol <alexandre@pujol.io>
# SPDX-License-Identifier: GPL-2.0-only

abi <abi/4.0>,

include <tunables/global>

@{exec_path} = @{bin}/os-prober
profile os-prober /{,usr/}bin/os-prober  flags=(attach_disconnected,complain) {
  include <abstractions/base>
  include <abstractions/consoles>
  include <abstractions/disks-read>

  capability dac_read_search,
  capability sys_admin,

  mount options=(rprivate, rw)      -> /,
  mount options=(rw, nosuid, nodev) -> /var/lib/os-prober/mount/,

  umount /var/lib/os-prober/mount/,

  mqueue (read getattr) type=posix /,

  @{exec_path} mrix,

  @{sh_path}               rix,
  @{bin}/{e,f,}grep        rix,
  @{sbin}/blkid            rpx,
  @{sbin}/btrfs            rpx,
  @{bin}/cat               rix,
  @{bin}/cut               rix,
  @{sbin}/dmraid           rpux,
  @{bin}/find              rix,
  @{bin}/grub-mount        rpx,
  @{sbin}/grub-probe       rpx,
  @{bin}/head              rix,
  @{bin}/kmod              rpx,
  @{bin}/logger            rix,
  @{bin}/ls                rix,
  @{bin}/lsblk             rpx,
  @{sbin}/lvm              rpx,
  @{bin}/mkdir             rix,
  @{bin}/mktemp            rix,
  @{bin}/mount             rix,
  @{sbin}/multipath        rpx,
  @{bin}/readlink          rix,
  @{bin}/rm                rix,
  @{bin}/rmdir             rix,
  @{bin}/sed               rix,
  @{bin}/udevadm           rpx,
  @{bin}/umount            rix,
  @{bin}/uname             rix,
  @{bin}/which{,.debianutils}  rix,
  @{lib}/newns             rix,
  @{lib}/os-prober/*       rix,
  @{lib}/os-probes/{,**}   rix,

  /usr/share/os-prober/common.sh r,
  /usr/share/terminfo/** r,

  /var/lib/os-prober/{,**} rw,

  @{MOUNTS}/ r,
  / r,
  @{efi}/ r,
  @{efi}/EFI/ r,
  @{efi}/EFI/**/ r,

  owner @{tmp}/os-prober.*/{,**} rw,

  @{run}/mount/utab r,

  @{sys}/devices/@{pci}/block/*/ r,
  @{sys}/devices/virtual/block/*/ r,

        @{PROC}/swaps r,
  owner @{PROC}/@{pid}/mountinfo r,
  owner @{PROC}/@{pid}/mounts r,

  /dev/tty@{int} rw,

  include if exists <local/os-prober>
}

# vim:syntax=apparmor
