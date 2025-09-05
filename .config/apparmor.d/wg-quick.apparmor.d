# apparmor.d - Full set of apparmor profiles
# Copyright (C) 2022-2024 Alexandre Pujol <alexandre@pujol.io>
# SPDX-License-Identifier: GPL-2.0-only

abi <abi/4.0>,

include <tunables/global>

@{exec_path} = @{bin}/wg-quick
profile wg-quick /{,usr/}bin/wg-quick  flags=(complain) {
  include <abstractions/base>
  include <abstractions/consoles>
  include <abstractions/nameservice-strict>

  capability dac_read_search,
  capability net_admin,

  network netlink raw,

  @{exec_path} mr,

  @{sh_path}                rix,
  @{bin}/cat                rix,
  @{bin}/ip                 rpx,
  @{bin}/mv                 rix,
  @{sbin}/nft               rix,
  @{bin}/readlink           rix,
  @{sbin}/resolvconf        rpx,
  @{bin}/resolvectl         rpx,
  @{bin}/rm                 rix,
  @{bin}/sort               rix,
  @{bin}/stat               rix,
  @{bin}/sync               rix,
  @{sbin}/sysctl            rcx -> sysctl,
  @{bin}/wg                 rpx,
  @{sbin}/xtables-nft-multi rix,

  /usr/share/terminfo/** r,

  /etc/iproute2/group  r,
  /etc/iproute2/rt_realms r,
  /etc/resolvconf/interface-order r,
  /etc/wireguard/{,**} rw,

  @{sys}/module/wireguard r,

  @{PROC}/@{pid}/net/ip_tables_names r,

  profile sysctl  flags=(complain) {
    include <abstractions/base>

    @{sbin}/sysctl mr,

    @{PROC}/sys/net/ipv4/conf/all/src_valid_mark w,

    include if exists <local/wg-quick_sysctl>
  }

  include if exists <local/wg-quick>
}

# vim:syntax=apparmor
