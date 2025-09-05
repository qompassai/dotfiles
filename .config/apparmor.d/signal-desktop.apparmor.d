# apparmor.d - Full set of apparmor profiles
# Copyright (C) 2018-2021 Mikhail Morfikov
# Copyright (C) 2023-2024 Alexandre Pujol <alexandre@pujol.io>
# SPDX-License-Identifier: GPL-2.0-only

abi <abi/4.0>,

include <tunables/global>

@{name} = signal-desktop{,-beta}
@{lib_dirs} = @{lib}/signal-desktop /opt/Signal{,?Beta}
@{config_dirs} = @{user_config_dirs}/Signal{,?Beta}
@{cache_dirs} = @{user_cache_dirs}/@{name}

@{exec_path} = @{lib_dirs}/@{name}
profile signal-desktop /{{,usr/}lib{,exec,32,64}/signal-desktop/signal-desktop{,-beta},opt/Signal{,?Beta}/signal-desktop{,-beta}} flags=(attach_disconnected,complain) {
  include <abstractions/base>
  include <abstractions/audio-client>
  include <abstractions/bus-session>
  include <abstractions/bus/org.freedesktop.ScreenSaver>
  include <abstractions/bus/org.kde.StatusNotifierWatcher>
  include <abstractions/common/electron>
  include <abstractions/devices-usb-read>
  include <abstractions/fontconfig-cache-read>
  include <abstractions/user-download-strict>
  include <abstractions/video>

  network inet dgram,
  network inet6 dgram,
  network inet stream,
  network inet6 stream,
  network netlink raw,

  @{exec_path} mrix,

  @{bin}/getconf       rix,
  @{open_path}         rpx -> child-open-strict,


  @{bin}/xdg-settings  rpx -> signal-desktop//&xdg-settings,

  audit @{lib_dirs}/chrome-sandbox rpx,
  @{lib_dirs}/chrome_crashpad_handler rix,

  @{att}/@{run}/systemd/inhibit/@{int}.ref rw,

        @{sys}/fs/cgroup/user.slice/cpu.max r,
        @{sys}/fs/cgroup/user.slice/user-@{uid}.slice/cpu.max r,
        @{sys}/fs/cgroup/user.slice/user-@{uid}.slice/session-@{word}.scope/memory.high r,
        @{sys}/fs/cgroup/user.slice/user-@{uid}.slice/session-@{word}.scope/memory.max r,
        @{sys}/fs/cgroup/user.slice/user-@{uid}.slice/user@@{uid}.service/cpu.max r,
  owner @{sys}/fs/cgroup/user.slice/user-@{uid}.slice/user@@{uid}.service/app.slice/cpu.max r,

  @{PROC}/@{pid}/fd/ r,
  @{PROC}/vmstat r,

  /dev/tty rw,

  # Stacked profile: xdg-settings
  include <abstractions/consoles>
  include <abstractions/freedesktop.org>
  @{sh_path}       rix,
  @{bin}/{,e}grep  rix,
  @{bin}/basename  rix,
  @{bin}/cat        ix,
  @{bin}/cut       rix,
  @{bin}/head       ix,
  @{bin}/mkdir      ix,
  @{bin}/mktemp     ix,
  @{bin}/mv         ix,
  @{bin}/readlink   ix,
  @{bin}/realpath  rix,
  @{bin}/rm         ix,
  @{bin}/sed        ix,
  @{bin}/sleep      ix,
  @{bin}/sort       ix,
  @{bin}/touch      ix,
  @{bin}/tr         ix,
  @{bin}/uname      ix,
  @{bin}/wc         ix,
  # To set/get DE information
  @{bin}/gconftool{,-2}       ix,
  @{bin}/kde{,4}-config       ix,
  @{bin}/kwriteconfig{,5,6}   ix,
  @{bin}/qtxdg-mat            ix,
  @{bin}/dbus-send            Cx -> bus,
  @{bin}/kreadconfig{,5}      Px,
  @{bin}/xdg-mime             Px,
  @{bin}/xprop                Px,
  owner @{user_config_dirs}/xfce4/helpers.rc{,.@{rand6}} rw,
  owner @{user_share_dirs}/applications/{,**} rw,
  @{PROC}/version r,
  owner /dev/pts/@{int} rw,
  profile bus flags=(complain) {
    include <abstractions/app/bus>
    include <abstractions/bus-session>
    include if exists <local/xdg-settings_bus>
  }
  include if exists <local/xdg-settings>

  include if exists <local/signal-desktop>
}

# vim:syntax=apparmor
