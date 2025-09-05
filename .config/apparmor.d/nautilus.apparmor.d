# apparmor.d - Full set of apparmor profiles
# Copyright (C) 2021-2024 Alexandre Pujol <alexandre@pujol.io>
# SPDX-License-Identifier: GPL-2.0-only

abi <abi/4.0>,

include <tunables/global>

@{exec_path} = @{bin}/nautilus
profile nautilus /{,usr/}bin/nautilus  flags=(attach_disconnected,complain) {
  include <abstractions/base>
  include <abstractions/bus-accessibility>
  include <abstractions/bus-session>
  include <abstractions/bus-system>
  include <abstractions/bus/com.canonical.Unity.LauncherEntry>
  include <abstractions/bus/org.a11y>
  include <abstractions/bus/org.freedesktop.hostname1>
  include <abstractions/bus/org.freedesktop.portal.Desktop>
  include <abstractions/bus/org.freedesktop.Tracker3.Miner.Files>
  include <abstractions/bus/org.gnome.SessionManager>
  include <abstractions/bus/org.gtk.Private.RemoteVolumeMonitor>
  include <abstractions/dconf-write>
  include <abstractions/deny-sensitive-home>
  include <abstractions/gnome-strict>
  include <abstractions/graphics>
  include <abstractions/nameservice-strict>
  include <abstractions/trash-strict>

  mqueue r type=posix /,

  unix type=stream peer=(label=gnome-shell),

  include <abstractions/bus/own-session>

  dbus bind bus=session name=org.freedesktop.FileManager1{,.*},
  dbus receive bus=session path=/org/freedesktop/FileManager1{,/**}
       interface=org.freedesktop.FileManager1{,.*}
       peer=(name="@{busname}"),
  dbus send bus=session path=/org/freedesktop/FileManager1{,/**}
       interface=org.freedesktop.FileManager1{,.*}
       peer=(name="{@{busname},org.freedesktop.DBus}"),
  dbus (send receive) bus=session path=/org/freedesktop/FileManager1{,/**}
       interface=org.freedesktop.DBus.Properties
       member={Get,GetAll,Set,PropertiesChanged}
       peer=(name="{@{busname},org.freedesktop.DBus}"),
  dbus receive bus=session path=/org/freedesktop/FileManager1{,/**}
       interface=org.freedesktop.DBus.Introspectable
       member=Introspect
       peer=(name="@{busname}"),
  dbus receive bus=session path=/org/freedesktop/FileManager1{,/**}
       interface=org.freedesktop.DBus.ObjectManager
       member=GetManagedObjects
       peer=(name="{@{busname},org.freedesktop.FileManager1{,.*}}"),
  dbus send bus=session path=/org/freedesktop/FileManager1{,/**}
       interface=org.freedesktop.DBus.ObjectManager
       member={InterfacesAdded,InterfacesRemoved}
       peer=(name="{@{busname},org.freedesktop.DBus}"),
  include <abstractions/bus/own-session>

  dbus bind bus=session name=org.gnome.Nautilus{,.*},
  dbus receive bus=session path=/org/gnome/Nautilus{,/**}
       interface=org.gnome.Nautilus{,.*}
       peer=(name="@{busname}"),
  dbus send bus=session path=/org/gnome/Nautilus{,/**}
       interface=org.gnome.Nautilus{,.*}
       peer=(name="{@{busname},org.freedesktop.DBus}"),
  dbus receive bus=session path=/org/gnome/Nautilus{,/**}
       interface="org.gtk.{Application,Actions}"
       peer=(name="@{busname}"),
  dbus send bus=session path=/org/gnome/Nautilus{,/**}
       interface="org.gtk.{Application,Actions}"
       peer=(name="{@{busname},org.freedesktop.DBus}"),
  dbus (send receive) bus=session path=/org/gnome/Nautilus{,/**}
       interface=org.freedesktop.DBus.Properties
       member={Get,GetAll,Set,PropertiesChanged}
       peer=(name="{@{busname},org.freedesktop.DBus}"),
  dbus receive bus=session path=/org/gnome/Nautilus{,/**}
       interface=org.freedesktop.DBus.Introspectable
       member=Introspect
       peer=(name="@{busname}"),
  dbus receive bus=session path=/org/gnome/Nautilus{,/**}
       interface=org.freedesktop.DBus.ObjectManager
       member=GetManagedObjects
       peer=(name="{@{busname},org.gnome.Nautilus{,.*}}"),
  dbus send bus=session path=/org/gnome/Nautilus{,/**}
       interface=org.freedesktop.DBus.ObjectManager
       member={InterfacesAdded,InterfacesRemoved}
       peer=(name="{@{busname},org.freedesktop.DBus}"),
  include <abstractions/bus/own-session>

  dbus bind bus=session name=org.gnome.Nautilus.SearchProvider{,.*},
  dbus receive bus=session path=/org/gnome/Nautilus/SearchProvider{,/**}
       interface=org.gnome.Nautilus.SearchProvider{,.*}
       peer=(name="@{busname}"),
  dbus send bus=session path=/org/gnome/Nautilus/SearchProvider{,/**}
       interface=org.gnome.Nautilus.SearchProvider{,.*}
       peer=(name="{@{busname},org.freedesktop.DBus}"),
  dbus receive bus=session path=/org/gnome/Nautilus/SearchProvider{,/**}
       interface=org.gnome.Shell.SearchProvider2
       peer=(name="@{busname}"),
  dbus send bus=session path=/org/gnome/Nautilus/SearchProvider{,/**}
       interface=org.gnome.Shell.SearchProvider2
       peer=(name="{@{busname},org.freedesktop.DBus}"),
  dbus (send receive) bus=session path=/org/gnome/Nautilus/SearchProvider{,/**}
       interface=org.freedesktop.DBus.Properties
       member={Get,GetAll,Set,PropertiesChanged}
       peer=(name="{@{busname},org.freedesktop.DBus}"),
  dbus receive bus=session path=/org/gnome/Nautilus/SearchProvider{,/**}
       interface=org.freedesktop.DBus.Introspectable
       member=Introspect
       peer=(name="@{busname}"),
  dbus receive bus=session path=/org/gnome/Nautilus/SearchProvider{,/**}
       interface=org.freedesktop.DBus.ObjectManager
       member=GetManagedObjects
       peer=(name="{@{busname},org.gnome.Nautilus.SearchProvider{,.*}}"),
  dbus send bus=session path=/org/gnome/Nautilus/SearchProvider{,/**}
       interface=org.freedesktop.DBus.ObjectManager
       member={InterfacesAdded,InterfacesRemoved}
       peer=(name="{@{busname},org.freedesktop.DBus}"),

  dbus (send receive) bus=session path=/org/gnome/Settings{,/**}
       interface=org.gnome.Settings{,.*}
       peer=(name="{@{busname},org.gnome.Settings{,.*}}", label=gnome-control-center),
  dbus (send receive) bus=session path=/org/gnome/Settings{,/**}
       interface=org.freedesktop.DBus.Properties
       member={Get,GetAll,Set,PropertiesChanged}
       peer=(name="{@{busname},org.gnome.Settings{,.*}}", label=gnome-control-center),
  dbus send bus=session path=/org/gnome/Settings{,/**}
       interface=org.freedesktop.DBus.Introspectable
       member=Introspect
       peer=(name="{@{busname},org.gnome.Settings{,.*}}", label=gnome-control-center),
  dbus send bus=session path=/org/gnome/Settings{,/**}
       interface=org.freedesktop.DBus.ObjectManager
       member=GetManagedObjects
       peer=(name="{@{busname},org.gnome.Settings{,.*}}", label=gnome-control-center),
  dbus receive bus=session path=/org/gnome/Settings{,/**}
       interface=org.freedesktop.DBus.ObjectManager
       member={InterfacesAdded,InterfacesRemoved}
       peer=(name="{@{busname},org.gnome.Settings{,.*}}", label=gnome-control-center),
  dbus (send receive) bus=session path=/org/gtk/MountOperationHandler{,/**}
       interface=org.gtk.MountOperationHandler{,.*}
       peer=(name="{@{busname},org.gtk.MountOperationHandler{,.*}}", label=gnome-shell),
  dbus (send receive) bus=session path=/org/gtk/MountOperationHandler{,/**}
       interface=org.freedesktop.DBus.Properties
       member={Get,GetAll,Set,PropertiesChanged}
       peer=(name="{@{busname},org.gtk.MountOperationHandler{,.*}}", label=gnome-shell),
  dbus send bus=session path=/org/gtk/MountOperationHandler{,/**}
       interface=org.freedesktop.DBus.Introspectable
       member=Introspect
       peer=(name="{@{busname},org.gtk.MountOperationHandler{,.*}}", label=gnome-shell),
  dbus send bus=session path=/org/gtk/MountOperationHandler{,/**}
       interface=org.freedesktop.DBus.ObjectManager
       member=GetManagedObjects
       peer=(name="{@{busname},org.gtk.MountOperationHandler{,.*}}", label=gnome-shell),
  dbus receive bus=session path=/org/gtk/MountOperationHandler{,/**}
       interface=org.freedesktop.DBus.ObjectManager
       member={InterfacesAdded,InterfacesRemoved}
       peer=(name="{@{busname},org.gtk.MountOperationHandler{,.*}}", label=gnome-shell),
  dbus (send receive) bus=session path=/org/gtk/Notifications{,/**}
       interface=org.gtk.Notifications{,.*}
       peer=(name="{@{busname},org.gtk.Notifications{,.*}}", label=gnome-shell),
  dbus (send receive) bus=session path=/org/gtk/Notifications{,/**}
       interface=org.freedesktop.DBus.Properties
       member={Get,GetAll,Set,PropertiesChanged}
       peer=(name="{@{busname},org.gtk.Notifications{,.*}}", label=gnome-shell),
  dbus send bus=session path=/org/gtk/Notifications{,/**}
       interface=org.freedesktop.DBus.Introspectable
       member=Introspect
       peer=(name="{@{busname},org.gtk.Notifications{,.*}}", label=gnome-shell),
  dbus send bus=session path=/org/gtk/Notifications{,/**}
       interface=org.freedesktop.DBus.ObjectManager
       member=GetManagedObjects
       peer=(name="{@{busname},org.gtk.Notifications{,.*}}", label=gnome-shell),
  dbus receive bus=session path=/org/gtk/Notifications{,/**}
       interface=org.freedesktop.DBus.ObjectManager
       member={InterfacesAdded,InterfacesRemoved}
       peer=(name="{@{busname},org.gtk.Notifications{,.*}}", label=gnome-shell),
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

  dbus send bus=session path=/org/gnome/Mutter/ServiceChannel
       interface=org.gnome.Mutter.ServiceChannel
       member=OpenWaylandServiceConnection
       peer=(name=@{busname}, label=gnome-shell),

  dbus (send, receive) bus=session path=/org/gtk/Application/CommandLine
       interface=org.gtk.private.CommandLine
       member=Print
       peer=(name=@{busname}, label=nautilus),

  dbus send bus=session path=/org/freedesktop/DBus
       interface=org.freedesktop.DBus
       member=ListActivatableNames
       peer=(name=org.freedesktop.DBus, label="@{p_dbus_session}"),

  dbus send bus=session path=/org/freedesktop/dbus
       interface=org.freedesktop.DBus
       member=NameHasOwner
       peer=(name=org.freedesktop.DBus, label="@{p_dbus_session}"),

  @{exec_path} mr,

  @{sh_path}                 rix,
  @{bin}/bwrap               rpx -> gnome-desktop-thumbnailers,
  @{bin}/file-roller         rpx,
  @{bin}/firejail           rpux,
  @{bin}/net                rpux,
  @{bin}/tracker3           rpux,

  @{open_path}               rpx -> child-open,

  /usr/share/nautilus/{,**} r,
  /usr/share/poppler/{,**} r,
  /usr/share/sounds/freedesktop/stereo/*.oga r,
  /usr/share/terminfo/** r,
  /usr/share/thumbnailers/{,**} r,
  /usr/share/tracker*/{,**} r,

  /etc/fstab r,

  /var/cache/fontconfig/ rw,

  #aa:lint ignore=too-wide
  # Full access to user's data
  / r,
  /*/ r,
  @{bin}/ r,
  @{lib}/ r,
  @{MOUNTDIRS}/ r,
  @{MOUNTS}/ r,
  @{MOUNTS}/** rw,
  owner @{HOME}/ r,
  owner @{HOME}/** rw,
  owner @{run}/user/@{uid}/ r,
  owner @{run}/user/@{uid}/** rw,
  owner @{tmp}/ r,
  owner @{tmp}/** rw,

  # Silence non user's data
  deny @{efi}/{,**} r,
  deny /opt/{,**} r,
  deny /root/{,**} r,
  deny /tmp/.* rw,
  deny /tmp/.*/{,**} rw,

  owner @{user_share_dirs}/nautilus/{,**} rwk,

  @{run}/mount/utab r,

  @{sys}/devices/**/hwmon@{int}/{,name,temp*,fan*} r,
  @{sys}/devices/**/hwmon@{int}/**/{,name,temp*,fan*} r,
  @{sys}/devices/**/hwmon/{,name,temp*,fan*} r,
  @{sys}/devices/**/hwmon/**/{,name,temp*,fan*} r,

        @{PROC}/@{pids}/net/wireless r,
        @{PROC}/sys/dev/i915/perf_stream_paranoid r,
  owner @{PROC}/@{pid}/cmdline r,
  owner @{PROC}/@{pid}/fd/ r,
  owner @{PROC}/@{pid}/mountinfo r,
  owner @{PROC}/@{pid}/stat r,
  owner @{PROC}/@{pid}/task/@{tid}/comm rw,

  /dev/tty rw,

  include if exists <local/nautilus>
}

# vim:syntax=apparmor
