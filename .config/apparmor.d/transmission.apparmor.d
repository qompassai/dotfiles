# apparmor.d - Full set of apparmor profiles
# Copyright (C) 2023-2024 Alexandre Pujol <alexandre@pujol.io>
# SPDX-License-Identifier: GPL-2.0-only

abi <abi/4.0>,

include <tunables/global>

@{exec_path} = @{bin}/transmission-{gtk,qt}
profile transmission /{,usr/}bin/transmission-{gtk,qt}  flags=(attach_disconnected,complain) {
  include <abstractions/base>
  include <abstractions/bus-accessibility>
  include <abstractions/bus-session>
  include <abstractions/bus/org.a11y>
  include <abstractions/bus/org.freedesktop.Notifications>
  include <abstractions/bus/org.kde.StatusNotifierWatcher>
  include <abstractions/dconf-write>
  include <abstractions/desktop>
  include <abstractions/graphics>
  include <abstractions/nameservice-strict>
  include <abstractions/ssl_certs>
  include <abstractions/trash-strict>
  include <abstractions/user-download-strict>

  network inet dgram,
  network inet6 dgram,
  network inet stream,
  network inet6 stream,
  network netlink raw,

  include <abstractions/bus/own-session>

  dbus bind bus=session name=com.transmissionbt.Transmission{,.*},
  dbus receive bus=session path=/com/transmissionbt/Transmission{,/**}
       interface=com.transmissionbt.Transmission{,.*}
       peer=(name="@{busname}"),
  dbus send bus=session path=/com/transmissionbt/Transmission{,/**}
       interface=com.transmissionbt.Transmission{,.*}
       peer=(name="{@{busname},org.freedesktop.DBus}"),
  dbus (send receive) bus=session path=/com/transmissionbt/Transmission{,/**}
       interface=org.freedesktop.DBus.Properties
       member={Get,GetAll,Set,PropertiesChanged}
       peer=(name="{@{busname},org.freedesktop.DBus}"),
  dbus receive bus=session path=/com/transmissionbt/Transmission{,/**}
       interface=org.freedesktop.DBus.Introspectable
       member=Introspect
       peer=(name="@{busname}"),
  dbus receive bus=session path=/com/transmissionbt/Transmission{,/**}
       interface=org.freedesktop.DBus.ObjectManager
       member=GetManagedObjects
       peer=(name="{@{busname},com.transmissionbt.Transmission{,.*}}"),
  dbus send bus=session path=/com/transmissionbt/Transmission{,/**}
       interface=org.freedesktop.DBus.ObjectManager
       member={InterfacesAdded,InterfacesRemoved}
       peer=(name="{@{busname},org.freedesktop.DBus}"),
  include <abstractions/bus/own-session>

  dbus bind bus=session name=com.transmissionbt.transmission_*{,.*},
  dbus receive bus=session path=/com/transmissionbt/transmission_*{,/**}
       interface=com.transmissionbt.transmission_*{,.*}
       peer=(name="@{busname}"),
  dbus send bus=session path=/com/transmissionbt/transmission_*{,/**}
       interface=com.transmissionbt.transmission_*{,.*}
       peer=(name="{@{busname},org.freedesktop.DBus}"),
  dbus (send receive) bus=session path=/com/transmissionbt/transmission_*{,/**}
       interface=org.freedesktop.DBus.Properties
       member={Get,GetAll,Set,PropertiesChanged}
       peer=(name="{@{busname},org.freedesktop.DBus}"),
  dbus receive bus=session path=/com/transmissionbt/transmission_*{,/**}
       interface=org.freedesktop.DBus.Introspectable
       member=Introspect
       peer=(name="@{busname}"),
  dbus receive bus=session path=/com/transmissionbt/transmission_*{,/**}
       interface=org.freedesktop.DBus.ObjectManager
       member=GetManagedObjects
       peer=(name="{@{busname},com.transmissionbt.transmission_*{,.*}}"),
  dbus send bus=session path=/com/transmissionbt/transmission_*{,/**}
       interface=org.freedesktop.DBus.ObjectManager
       member={InterfacesAdded,InterfacesRemoved}
       peer=(name="{@{busname},org.freedesktop.DBus}"),
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

  @{exec_path} mr,

  @{open_path}         rpx -> child-open,

  /usr/share/transmission/{,**} r,

  owner @{HOME}/ r,

  owner @{user_torrents_dirs}/ r,
  owner @{user_torrents_dirs}/** rw,

  owner @{user_config_dirs}/transmission/ rw,
  owner @{user_config_dirs}/transmission/** rwk,

  owner @{user_cache_dirs}/transmission/ rw,
  owner @{user_cache_dirs}/transmission/** rwk,

  owner @{tmp}/tr_session_id_* rwk,

  @{run}/mount/utab r,

        @{PROC}/@{pid}/net/route r,
        @{PROC}/sys/net/ipv6/conf/all/disable_ipv6 r,
  owner @{PROC}/@{pid}/cmdline r,
  owner @{PROC}/@{pid}/comm r,
  owner @{PROC}/@{pid}/mountinfo r,
  owner @{PROC}/@{pid}/mounts r,
  owner @{PROC}/@{pid}/stat r,
  owner @{PROC}/@{pid}/task/@{tid}/comm rw,

  deny @{user_share_dirs}/gvfs-metadata/* r,

  include if exists <local/transmission>
}

# vim:syntax=apparmor
