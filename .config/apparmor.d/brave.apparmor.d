# apparmor.d - Full set of apparmor profiles
# Copyright (C) 2019-2021 Mikhail Morfikov
# Copyright (C) 2021-2024 Alexandre Pujol <alexandre@pujol.io>
# SPDX-License-Identifier: GPL-2.0-only

abi <abi/4.0>,

include <tunables/global>

@{name} = brave{,-beta,-dev,-bin}
@{domain} = com.brave.Brave org.chromium.Chromium
@{lib_dirs} = /opt/brave{-bin,.com}{,/@{name}}
@{config_dirs} = @{user_config_dirs}/BraveSoftware/Brave-Browser{,-Beta,-Dev}
@{cache_dirs} = @{user_cache_dirs}/BraveSoftware/Brave-Browser{,-Beta,-Dev}

@{exec_path} = @{lib_dirs}/@{name}
profile brave /opt/brave{-bin,.com}{,/brave{,-beta,-dev,-bin}}/brave{,-beta,-dev,-bin}  flags=(attach_disconnected,complain) {
  include <abstractions/base>
  include <abstractions/app/chromium>

  unix (send, receive) type=stream peer=(label=brave//&brave-crashpad-handler),

  signal receive peer=brave//&brave-crashpad-handler,

  include <abstractions/bus/own-session>

  dbus bind bus=session name=org.mpris.MediaPlayer2.brave{,.*},
  dbus receive bus=session path=/org/mpris/MediaPlayer2
       interface=org.mpris.MediaPlayer2.brave{,.*}
       peer=(name="@{busname}"),
  dbus send bus=session path=/org/mpris/MediaPlayer2
       interface=org.mpris.MediaPlayer2.brave{,.*}
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
       peer=(name="{@{busname},org.mpris.MediaPlayer2.brave{,.*}}"),
  dbus send bus=session path=/org/mpris/MediaPlayer2
       interface=org.freedesktop.DBus.ObjectManager
       member={InterfacesAdded,InterfacesRemoved}
       peer=(name="{@{busname},org.freedesktop.DBus}"),

  @{exec_path} mrix,

  @{bin}/man  rpux, #  For "brave --help"

  @{lib_dirs}/chrome_crashpad_handler  rpx -> brave//&brave-crashpad-handler,

  /usr/share/chromium/extensions/ r,

  /etc/opt/chrome/ r,
  /etc/opt/chrome/native-messaging-hosts/* r,

  owner @{user_config_dirs}/BraveSoftware/ rw,

  owner @{config_dirs}/WidevineCdm/libwidevinecdm.so mrw,
  owner @{cache_dirs}/BraveSoftware/ rw,

  owner @{tmp}/net-export/ rw,  # For brave://net-export/

  # Silencer
  deny /etc/opt/ w,
  deny /etc/opt/chrome/ w,
  deny /dev/disk/by-uuid/ r,

  include if exists <local/brave>
}

# vim:syntax=apparmor
