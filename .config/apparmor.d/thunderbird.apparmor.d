# apparmor.d - Full set of apparmor profiles
# Copyright (C) 2015-2021 Mikhail Morfikov
# Copyright (C) 2021-2024 Alexandre Pujol <alexandre@pujol.io>
# SPDX-License-Identifier: GPL-2.0-only

abi <abi/4.0>,

include <tunables/global>

@{name} = thunderbird{,-bin}
@{lib_dirs} = @{lib}/@{name}
@{config_dirs} = @{HOME}/.@{name}/
@{cache_dirs} = @{user_cache_dirs}/@{name}/

@{exec_path} = @{bin}/@{name} @{lib_dirs}/@{name}
profile thunderbird /{{,usr/}bin/thunderbird{,-bin},{,usr/}lib{,exec,32,64}/thunderbird{,-bin}/thunderbird{,-bin}} flags=(complain) {
  include <abstractions/base>
  include <abstractions/app/firefox>
  include <abstractions/user-download-strict>
  include <abstractions/user-read-strict>

  include <abstractions/bus/own-session>

  dbus bind bus=session name=org.mozilla.thunderbird{,.*},
  dbus receive bus=session path=/org/mozilla/thunderbird{,/**}
       interface=org.mozilla.thunderbird{,.*}
       peer=(name="@{busname}"),
  dbus send bus=session path=/org/mozilla/thunderbird{,/**}
       interface=org.mozilla.thunderbird{,.*}
       peer=(name="{@{busname},org.freedesktop.DBus}"),
  dbus (send receive) bus=session path=/org/mozilla/thunderbird{,/**}
       interface=org.freedesktop.DBus.Properties
       member={Get,GetAll,Set,PropertiesChanged}
       peer=(name="{@{busname},org.freedesktop.DBus}"),
  dbus receive bus=session path=/org/mozilla/thunderbird{,/**}
       interface=org.freedesktop.DBus.Introspectable
       member=Introspect
       peer=(name="@{busname}"),
  dbus receive bus=session path=/org/mozilla/thunderbird{,/**}
       interface=org.freedesktop.DBus.ObjectManager
       member=GetManagedObjects
       peer=(name="{@{busname},org.mozilla.thunderbird{,.*}}"),
  dbus send bus=session path=/org/mozilla/thunderbird{,/**}
       interface=org.freedesktop.DBus.ObjectManager
       member={InterfacesAdded,InterfacesRemoved}
       peer=(name="{@{busname},org.freedesktop.DBus}"),

  @{exec_path} mrix,

  @{lib_dirs}/glxtest    rpx,
  @{lib_dirs}/vaapitest  rpx,

  @{lib}/@{multiarch}/qt5/plugins/kf5/org.kde.kwindowsystem.platforms/KF5WindowSystemKWaylandPlugin.so mr,
  @{lib}/@{multiarch}/qt5/plugins/kf5/org.kde.kwindowsystem.platforms/KF5WindowSystemX11Plugin.so mr,

  # GPG integration
  @{bin}/gpg{,2}     rpx,
  @{bin}/gpgconf     rpx,
  @{bin}/gpgsm       rpx,

  # Desktop integration
  @{open_path}       rpx -> child-open,

  # Extensions
  @{bin}/SysTray-X   rpux,

  /usr/share/lightning/{,**} r,

  owner /var/mail/** rwk,

  owner @{user_mail_dirs}/ rw,
  owner @{user_mail_dirs}/** rwl -> @{user_mail_dirs}/**,

  owner @{user_config_dirs}/gtk-{3,4}.0/assets/*.svg r,
  owner @{user_config_dirs}/ibus/bus/ r,
  owner @{user_config_dirs}/ibus/bus/@{hex32}-unix-{,wayland-}@{int} r,
  owner @{user_config_dirs}/kioslaverc r,
  owner @{user_config_dirs}/mimeapps.list{,.@{rand6}} rw,

  owner @{tmp}/MozillaMailnews/ rw,
  owner @{tmp}/MozillaMailnews/*.msf rw,
  owner @{tmp}/nscopy.tmp rw,
  owner @{tmp}/nsemail{,-@{int}}.eml rw,
  owner @{tmp}/nsma{,-@{int}} rw,
  owner @{tmp}/pid-@{pid}/{,**} w,
  owner @{tmp}/remote-settings-startup-bundle- rw,

  /dev/urandom w,

  # Silencer
  deny capability sys_ptrace,
  deny @{lib_dirs}/** w,
  deny @{lib_dirs}/crashreporter x,
  deny @{lib_dirs}/minidump-analyzer x,
  deny @{HOME}/.mozilla/** mrwkl,

  include if exists <local/thunderbird>
}

# vim:syntax=apparmor
