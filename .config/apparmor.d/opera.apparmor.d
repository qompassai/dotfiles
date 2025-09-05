# apparmor.d - Full set of apparmor profiles
# Copyright (C) 2018-2021 Mikhail Morfikov
# Copyright (C) 2021-2024 Alexandre Pujol <alexandre@pujol.io>
# SPDX-License-Identifier: GPL-2.0-only

abi <abi/4.0>,

include <tunables/global>

@{name} = opera{,-beta,-developer}
@{domain} = com.opera.Opera
@{lib_dirs} = @{lib}/@{multiarch}/@{name}
@{config_dirs} = @{user_config_dirs}/@{name}
@{cache_dirs} = @{user_cache_dirs}/@{name}

@{exec_path} = @{lib_dirs}/@{name}
profile opera /{,usr/}lib{,exec,32,64}/*-linux-gnu*/opera{,-beta,-developer}/opera{,-beta,-developer} flags=(complain) {
  include <abstractions/base>
  include <abstractions/app/chromium>

  include <abstractions/bus/own-session>

  dbus bind bus=session name=org.mpris.MediaPlayer2.opera{,.*},
  dbus receive bus=session path=/org/mpris/MediaPlayer2
       interface=org.mpris.MediaPlayer2.opera{,.*}
       peer=(name="@{busname}"),
  dbus send bus=session path=/org/mpris/MediaPlayer2
       interface=org.mpris.MediaPlayer2.opera{,.*}
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
       peer=(name="{@{busname},org.mpris.MediaPlayer2.opera{,.*}}"),
  dbus send bus=session path=/org/mpris/MediaPlayer2
       interface=org.freedesktop.DBus.ObjectManager
       member={InterfacesAdded,InterfacesRemoved}
       peer=(name="{@{busname},org.freedesktop.DBus}"),

  @{exec_path} mrix,

  @{lib_dirs}/opera_autoupdate    krix,
  @{lib_dirs}/opera_crashreporter  rpx,
  @{lib_dirs}/opera-sandbox        rpx,

  /opt/google/chrome{,-beta,-unstable}/libwidevinecdm.so mr,
  /opt/google/chrome{,-beta,-unstable}/libwidevinecdmadapter.so mr,

  include if exists <local/opera>
}

# vim:syntax=apparmor
