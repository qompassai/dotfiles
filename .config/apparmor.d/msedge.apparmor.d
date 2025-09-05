# apparmor.d - Full set of apparmor profiles
# Copyright (C) 2022-2024 Alexandre Pujol <alexandre@pujol.io>
# Copyright (C) 2022-2024 Jose Maldonado <josemald89@gmail.com>
# SPDX-License-Identifier: GPL-2.0-only

abi <abi/4.0>,

include <tunables/global>

@{name} = msedge{,-beta,-dev}
@{domain} = com.microsoft.Edge
@{lib_dirs} = /opt/microsoft/@{name}
@{config_dirs} = @{user_config_dirs}/microsoft-edge{,-beta,-dev}
@{cache_dirs} = @{user_cache_dirs}/microsoft-edge{,-beta,-dev}

@{exec_path} = @{lib_dirs}/@{name}
profile msedge /opt/microsoft/msedge{,-beta,-dev}/msedge{,-beta,-dev} flags=(complain) {
  include <abstractions/base>
  include <abstractions/app/chromium>

  include <abstractions/bus/own-session>

  dbus bind bus=session name=org.mpris.MediaPlayer2.msedge{,.*},
  dbus receive bus=session path=/org/mpris/MediaPlayer2
       interface=org.mpris.MediaPlayer2.msedge{,.*}
       peer=(name="@{busname}"),
  dbus send bus=session path=/org/mpris/MediaPlayer2
       interface=org.mpris.MediaPlayer2.msedge{,.*}
       peer=(name="{@{busname},org.freedesktop.DBus}"),
  dbus (send receive) bus=session path=/org/mpris/MediaPlayer2
       interface=org.freedesktop.DBus.Properties
       member={Get,GetAll,Set,PropertiesChanged}
       peer=(name="{@{busname},org.freedesktop.DBus}"),
  dbus receive bus=session path=/org/mpris/MediaPlayer2
       interface=org.freedesktop.DBus.Introspectable
       member=Introspect
       peer=(name="@{busname}"),
  dbus receive bus=session path=/org/mpris/MediaPlayer2
       interface=org.freedesktop.DBus.ObjectManager
       member=GetManagedObjects
       peer=(name="{@{busname},org.mpris.MediaPlayer2.msedge{,.*}}"),
  dbus send bus=session path=/org/mpris/MediaPlayer2
       interface=org.freedesktop.DBus.ObjectManager
       member={InterfacesAdded,InterfacesRemoved}
       peer=(name="{@{busname},org.freedesktop.DBus}"),

  @{exec_path} mrix,

  @{bin}/man  rpux, #  For "chrome --help"

  @{lib_dirs}/xdg-mime       rix, #-> xdg-mime,
  @{lib_dirs}/xdg-settings   rix, #-> xdg-settings,

  @{lib_dirs}/microsoft-edge{,beta,-dev}  rpx,
  @{lib_dirs}/chrome_crashpad_handler  rpx -> msedge//&msedge-crashpad-handler,

  @{lib_dirs}/*.so* mr,
  @{lib_dirs}/WidevineCdm/_platform_specific/linux_*/libwidevinecdm.so mr,

  owner @{user_cache_dirs}/Microsoft/ rw,
  owner @{user_cache_dirs}/Microsoft/** rwk,

  owner @{tmp}/.ses rw,
  owner @{tmp}/cv_debug.log rw,

  include if exists <local/msedge>
}

# vim:syntax=apparmor
