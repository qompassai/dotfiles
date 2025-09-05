# apparmor.d - Full set of apparmor profiles
# Copyright (C) 2018-2021 Mikhail Morfikov
# Copyright (C) 2022-2024 Alexandre Pujol <alexandre@pujol.io>
# SPDX-License-Identifier: GPL-2.0-only

abi <abi/4.0>,

include <tunables/global>

@{name} = chrome{,-beta,-stable,-unstable}
@{domain} = com.google.Chrome
@{lib_dirs} = /opt/google/@{name}
@{config_dirs} = @{user_config_dirs}/google-@{name}
@{cache_dirs} = @{user_cache_dirs}/google-@{name}

@{exec_path} = @{lib_dirs}/@{name}
profile chrome /opt/google/chrome{,-beta,-stable,-unstable}/chrome{,-beta,-stable,-unstable}  flags=(attach_disconnected,complain) {
  include <abstractions/base>
  include <abstractions/app/chromium>

  include <abstractions/bus/own-session>

  dbus bind bus=session name=org.mpris.MediaPlayer2.chrome{,.*},
  dbus receive bus=session path=/org/mpris/MediaPlayer2
       interface=org.mpris.MediaPlayer2.chrome{,.*}
       peer=(name="@{busname}"),
  dbus send bus=session path=/org/mpris/MediaPlayer2
       interface=org.mpris.MediaPlayer2.chrome{,.*}
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
       peer=(name="{@{busname},org.mpris.MediaPlayer2.chrome{,.*}}"),
  dbus send bus=session path=/org/mpris/MediaPlayer2
       interface=org.freedesktop.DBus.ObjectManager
       member={InterfacesAdded,InterfacesRemoved}
       peer=(name="{@{busname},org.freedesktop.DBus}"),

  @{exec_path} mrix,

  @{bin}/man  rpux, #  For "chrome --help"

  @{lib_dirs}/chrome_crashpad_handler  rpx -> chrome//&chrome-crashpad-handler,
  @{lib_dirs}/google-@{name}  rpx,

  @{lib_dirs}/nacl_helper    rix,
  @{lib_dirs}/xdg-mime       rix, #-> xdg-mime,
  @{lib_dirs}/xdg-settings   rix, #-> xdg-settings,

  @{lib_dirs}/*.so* mr,
  @{lib_dirs}/libwidevinecdm.so mr,
  @{lib_dirs}/libwidevinecdmadapter.so mr,
  @{lib_dirs}/WidevineCdm/_platform_specific/linux_*/libwidevinecdm.so mr,

  include if exists <local/chrome>
}

# vim:syntax=apparmor
