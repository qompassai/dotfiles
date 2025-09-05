# apparmor.d - Full set of apparmor profiles
# Copyright (C) 2023-2024 Alexandre Pujol <alexandre@pujol.io>
# SPDX-License-Identifier: GPL-2.0-only

abi <abi/4.0>,

include <tunables/global>

@{exec_path} = @{bin}/remmina
profile remmina /{,usr/}bin/remmina flags=(complain) {
  include <abstractions/base>
  include <abstractions/audio-client>
  include <abstractions/bus-accessibility>
  include <abstractions/bus-session>
  include <abstractions/bus-system>
  include <abstractions/bus/org.a11y>
  include <abstractions/bus/org.freedesktop.Avahi>
  include <abstractions/bus/org.freedesktop.hostname1>
  include <abstractions/bus/org.freedesktop.Notifications>
  include <abstractions/bus/org.freedesktop.secrets>
  include <abstractions/bus/org.gtk.Private.RemoteVolumeMonitor>
  include <abstractions/bus/org.kde.StatusNotifierWatcher>
  include <abstractions/dconf-write>
  include <abstractions/desktop>
  include <abstractions/fontconfig-cache-read>
  include <abstractions/ibus>
  include <abstractions/nameservice-strict>
  include <abstractions/ssl_certs>
  include <abstractions/thumbnails-cache-read>
  include <abstractions/user-download-strict>

  network inet stream,
  network inet6 stream,
  network inet dgram,
  network inet6 dgram,
  network netlink raw,

  include <abstractions/bus/own-session>

  dbus bind bus=session name=org.remmina.Remmina{,.*},
  dbus receive bus=session path=/org/remmina/Remmina{,/**}
       interface=org.remmina.Remmina{,.*}
       peer=(name="@{busname}"),
  dbus send bus=session path=/org/remmina/Remmina{,/**}
       interface=org.remmina.Remmina{,.*}
       peer=(name="{@{busname},org.freedesktop.DBus}"),
  dbus receive bus=session path=/org/remmina/Remmina{,/**}
       interface=org.gtk.Actions
       peer=(name="@{busname}"),
  dbus send bus=session path=/org/remmina/Remmina{,/**}
       interface=org.gtk.Actions
       peer=(name="{@{busname},org.freedesktop.DBus}"),
  dbus (send receive) bus=session path=/org/remmina/Remmina{,/**}
       interface=org.freedesktop.DBus.Properties
       member={Get,GetAll,Set,PropertiesChanged}
       peer=(name="{@{busname},org.freedesktop.DBus}"),
  dbus receive bus=session path=/org/remmina/Remmina{,/**}
       interface=org.freedesktop.DBus.Introspectable
       member=Introspect
       peer=(name="@{busname}"),
  dbus receive bus=session path=/org/remmina/Remmina{,/**}
       interface=org.freedesktop.DBus.ObjectManager
       member=GetManagedObjects
       peer=(name="{@{busname},org.remmina.Remmina{,.*}}"),
  dbus send bus=session path=/org/remmina/Remmina{,/**}
       interface=org.freedesktop.DBus.ObjectManager
       member={InterfacesAdded,InterfacesRemoved}
       peer=(name="{@{busname},org.freedesktop.DBus}"),
  dbus (send receive) bus=session path=/org/ayatana/NotificationItem{,/**}
       interface=org.ayatana.NotificationItem{,.*}
       peer=(name="{@{busname},org.ayatana.NotificationItem{,.*}}", label=gnome-shell),
  dbus (send receive) bus=session path=/org/ayatana/NotificationItem{,/**}
       interface=org.freedesktop.DBus.Properties
       member={Get,GetAll,Set,PropertiesChanged}
       peer=(name="{@{busname},org.ayatana.NotificationItem{,.*}}", label=gnome-shell),
  dbus send bus=session path=/org/ayatana/NotificationItem{,/**}
       interface=org.freedesktop.DBus.Introspectable
       member=Introspect
       peer=(name="{@{busname},org.ayatana.NotificationItem{,.*}}", label=gnome-shell),
  dbus send bus=session path=/org/ayatana/NotificationItem{,/**}
       interface=org.freedesktop.DBus.ObjectManager
       member=GetManagedObjects
       peer=(name="{@{busname},org.ayatana.NotificationItem{,.*}}", label=gnome-shell),
  dbus receive bus=session path=/org/ayatana/NotificationItem{,/**}
       interface=org.freedesktop.DBus.ObjectManager
       member={InterfacesAdded,InterfacesRemoved}
       peer=(name="{@{busname},org.ayatana.NotificationItem{,.*}}", label=gnome-shell),
  dbus (send receive) bus=session path=/org/gtk/vfs{,/**}
       interface=org.gtk.vfs{,.*}
       peer=(name="{@{busname},org.gtk.vfs{,.*}}", label="gvfsd{,-*}"),
  dbus (send receive) bus=session path=/org/gtk/vfs{,/**}
       interface=org.freedesktop.DBus.Properties
       member={Get,GetAll,Set,PropertiesChanged}
       peer=(name="{@{busname},org.gtk.vfs{,.*}}", label="gvfsd{,-*}"),
  dbus send bus=session path=/org/gtk/vfs{,/**}
       interface=org.freedesktop.DBus.Introspectable
       member=Introspect
       peer=(name="{@{busname},org.gtk.vfs{,.*}}", label="gvfsd{,-*}"),
  dbus send bus=session path=/org/gtk/vfs{,/**}
       interface=org.freedesktop.DBus.ObjectManager
       member=GetManagedObjects
       peer=(name="{@{busname},org.gtk.vfs{,.*}}", label="gvfsd{,-*}"),
  dbus receive bus=session path=/org/gtk/vfs{,/**}
       interface=org.freedesktop.DBus.ObjectManager
       member={InterfacesAdded,InterfacesRemoved}
       peer=(name="{@{busname},org.gtk.vfs{,.*}}", label="gvfsd{,-*}"),

  @{exec_path} rm,

  @{open_path} rpx -> child-open-browsers,

  /usr/share/remmina/{,**} r,
  /usr/share/themes/{,**} r,

  /etc/fstab r,
  /etc/ssh/ssh_config r,
  /etc/ssh/ssh_config.d/{,*} r,
  /etc/timezone r,

  owner @{HOME}/@{XDG_SSH_DIR}/config r,
  owner @{HOME}/@{XDG_SSH_DIR}/known_hosts r,

  owner @{user_cache_dirs}/org.remmina.Remmina/{,**} rw,
  owner @{user_cache_dirs}/remmina/{,**} rw,
  owner @{user_config_dirs}/autostart/remmina-applet.desktop r,
  owner @{user_config_dirs}/freerdp/known_hosts2 rwk,
  owner @{user_config_dirs}/remmina/{,**} rw,
  owner @{user_share_dirs}/remmina/{,**} rw,

  owner @{PROC}/@{pid}/task/@{tid}/comm rw,
  owner @{PROC}/@{pid}/mountinfo r,

  owner @{run}/user/@{uid}/keyring/ssh rw,

  @{sys}/devices/system/node/ r,
  @{sys}/devices/system/node/node@{int}/meminfo r,

  include if exists <local/remmina>
}

# vim:syntax=apparmor
