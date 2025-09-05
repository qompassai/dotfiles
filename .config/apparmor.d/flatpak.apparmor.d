# apparmor.d - Full set of apparmor profiles
# Copyright (C) 2023-2024 Alexandre Pujol <alexandre@pujol.io>
# SPDX-License-Identifier: GPL-2.0-only

abi <abi/4.0>,

include <tunables/global>

@{exec_path} = @{bin}/flatpak
profile flatpak /{,usr/}bin/flatpak  flags=(attach_disconnected,mediate_deleted,complain) {
  include <abstractions/base>
  include <abstractions/bus-accessibility>
  include <abstractions/bus-session>
  include <abstractions/bus-system>
  include <abstractions/bus/org.a11y>
  include <abstractions/bus/org.freedesktop.locale1>
  include <abstractions/bus/org.gtk.vfs.MountTracker>
  include <abstractions/consoles>
  include <abstractions/dconf-write>
  include <abstractions/desktop>
  include <abstractions/nameservice-strict>
  include <abstractions/ssl_certs>

  userns,

  capability dac_override,
  capability dac_read_search,
  capability net_admin,
  capability sys_ptrace,

  network inet dgram,
  network inet6 dgram,
  network inet stream,
  network inet6 stream,
  network netlink raw,

  mount fstype=fuse.revokefs-fuse options=(rw, nosuid, nodev) -> /var/tmp/flatpak-cache-*/*/,

  ptrace (read) peer=flatpak-app,

  signal send peer=flatpak-app,

  dbus (send receive) bus=session path=/org/freedesktop/Flatpak/SessionHelper{,/**}
       interface=org.freedesktop.Flatpak.SessionHelper{,.*}
       peer=(name="{@{busname},org.freedesktop.Flatpak.SessionHelper{,.*}}", label=flatpak-session-helper),
  dbus (send receive) bus=session path=/org/freedesktop/Flatpak/SessionHelper{,/**}
       interface=org.freedesktop.DBus.Properties
       member={Get,GetAll,Set,PropertiesChanged}
       peer=(name="{@{busname},org.freedesktop.Flatpak.SessionHelper{,.*}}", label=flatpak-session-helper),
  dbus send bus=session path=/org/freedesktop/Flatpak/SessionHelper{,/**}
       interface=org.freedesktop.DBus.Introspectable
       member=Introspect
       peer=(name="{@{busname},org.freedesktop.Flatpak.SessionHelper{,.*}}", label=flatpak-session-helper),
  dbus send bus=session path=/org/freedesktop/Flatpak/SessionHelper{,/**}
       interface=org.freedesktop.DBus.ObjectManager
       member=GetManagedObjects
       peer=(name="{@{busname},org.freedesktop.Flatpak.SessionHelper{,.*}}", label=flatpak-session-helper),
  dbus receive bus=session path=/org/freedesktop/Flatpak/SessionHelper{,/**}
       interface=org.freedesktop.DBus.ObjectManager
       member={InterfacesAdded,InterfacesRemoved}
       peer=(name="{@{busname},org.freedesktop.Flatpak.SessionHelper{,.*}}", label=flatpak-session-helper),
  dbus (send receive) bus=system path=/org/freedesktop/Accounts{,/**}
       interface=org.freedesktop.Accounts{,.*}
       peer=(name="{@{busname},org.freedesktop.Accounts{,.*}}", label="@{p_accounts_daemon}"),
  dbus (send receive) bus=system path=/org/freedesktop/Accounts{,/**}
       interface=org.freedesktop.DBus.Properties
       member={Get,GetAll,Set,PropertiesChanged}
       peer=(name="{@{busname},org.freedesktop.Accounts{,.*}}", label="@{p_accounts_daemon}"),
  dbus send bus=system path=/org/freedesktop/Accounts{,/**}
       interface=org.freedesktop.DBus.Introspectable
       member=Introspect
       peer=(name="{@{busname},org.freedesktop.Accounts{,.*}}", label="@{p_accounts_daemon}"),
  dbus send bus=system path=/org/freedesktop/Accounts{,/**}
       interface=org.freedesktop.DBus.ObjectManager
       member=GetManagedObjects
       peer=(name="{@{busname},org.freedesktop.Accounts{,.*}}", label="@{p_accounts_daemon}"),
  dbus receive bus=system path=/org/freedesktop/Accounts{,/**}
       interface=org.freedesktop.DBus.ObjectManager
       member={InterfacesAdded,InterfacesRemoved}
       peer=(name="{@{busname},org.freedesktop.Accounts{,.*}}", label="@{p_accounts_daemon}"),
  dbus (send receive) bus=system path=/org/freedesktop/PolicyKit1{,/**}
       interface=org.freedesktop.PolicyKit1{,.*}
       peer=(name="{@{busname},org.freedesktop.PolicyKit1{,.*}}", label="@{p_polkitd}"),
  dbus (send receive) bus=system path=/org/freedesktop/PolicyKit1{,/**}
       interface=org.freedesktop.DBus.Properties
       member={Get,GetAll,Set,PropertiesChanged}
       peer=(name="{@{busname},org.freedesktop.PolicyKit1{,.*}}", label="@{p_polkitd}"),
  dbus send bus=system path=/org/freedesktop/PolicyKit1{,/**}
       interface=org.freedesktop.DBus.Introspectable
       member=Introspect
       peer=(name="{@{busname},org.freedesktop.PolicyKit1{,.*}}", label="@{p_polkitd}"),
  dbus send bus=system path=/org/freedesktop/PolicyKit1{,/**}
       interface=org.freedesktop.DBus.ObjectManager
       member=GetManagedObjects
       peer=(name="{@{busname},org.freedesktop.PolicyKit1{,.*}}", label="@{p_polkitd}"),
  dbus receive bus=system path=/org/freedesktop/PolicyKit1{,/**}
       interface=org.freedesktop.DBus.ObjectManager
       member={InterfacesAdded,InterfacesRemoved}
       peer=(name="{@{busname},org.freedesktop.PolicyKit1{,.*}}", label="@{p_polkitd}"),

  dbus send bus=session path=/org/freedesktop/portal/documents
       interface=org.freedesktop.portal.Documents
       member=GetMountPoint
       peer=(name=org.freedesktop.portal.Documents, label="{xdg-document-portal,unconfined}"),

  @{exec_path} mr,

  @{bin}/bwrap               rpx -> flatpak-app,
  @{bin}/fusermount{,3}      rcx -> fusermount,
  @{bin}/gpg                 rcx -> gpg,
  @{bin}/gpgconf             rcx -> gpg,
  @{bin}/gpgsm               rcx -> gpg,
  @{lib}/revokefs-fuse       rix,

  @{lib}/polkit-[0-9]/polkit-agent-helper-[0-9]  rpx,
  @{lib}/polkit-agent-helper-[0-9]               rpx,

  /usr/share/flatpak/{,**} r,

  /etc/flatpak/{,**} r,
  /etc/pulse/client.conf r,

  / r,

  /var/lib/flatpak/{,**} rwlk,

        /var/tmp/#@{int} rw,
        /var/tmp/flatpak-cache-@{rand6}/{,**/} r,
  owner /var/tmp/flatpak-cache-@{rand6}/ rw,
  owner /var/tmp/flatpak-cache-@{rand6}/** rwlk -> /var/tmp/flatpak-cache-@{rand6}/**,

  owner @{HOME}/.var/ w,
  owner @{HOME}/.var/app/{,**} rw,

  # Can create dotfile directories for any app
  owner @{user_cache_dirs}/*/ w,
  owner @{user_config_dirs}/*/ w,
  owner @{user_share_dirs}/*/ w,
  owner @{user_games_dirs}/{,**/} w,
  owner @{user_documents_dirs}/ w,

  owner @{user_cache_dirs}/flatpak/{,**} rw,
  owner @{user_config_dirs}/pulse/client.conf r,
  owner @{user_config_dirs}/user-dirs.dirs r,

        @{user_share_dirs}/flatpak/{,**} r,
  owner @{user_share_dirs}/ r,
  owner @{user_share_dirs}/flatpak/ rw,
  owner @{user_share_dirs}/flatpak/** rwlk,

  owner @{tmp}/#@{int} rw,
  owner @{tmp}/ostree-gpg-@{rand6}/{,**} rw,
  owner @{tmp}/remote-summary-sig.@{rand6} rw,
  owner @{tmp}/remote-summary.@{rand6} rw,
  owner /dev/shm/flatpak*/{,**} rw,

         @{run}/.userns r,
  @{att}/@{run}/.userns r,

        @{run}/user/@{uid}/.dbus-proxy/ w,
        @{run}/user/@{uid}/dconf/user rw,
  owner @{run}/user/@{uid}/.dbus-proxy/* rw,
  owner @{run}/user/@{uid}/.flatpak-cache rw,
  owner @{run}/user/@{uid}/.flatpak/ rw,
  owner @{run}/user/@{uid}/.flatpak/** rwlk -> @{run}/user/@{uid}/.flatpak/**,
  owner @{run}/user/@{uid}/app/ w,
  owner @{run}/user/@{uid}/app/*/ w,
  owner @{run}/user/@{uid}/systemd/private rw,

  @{sys}/module/nvidia/version r,

        @{PROC}/sys/fs/pipe-max-size r,
  owner @{PROC}/@{pid}/fdinfo/@{int} r,
  owner @{PROC}/@{pid}/stat r,

  /dev/fuse rw,
  /dev/tty rw,
  /dev/tty@{int} rw,

  deny owner @{user_share_dirs}/gvfs-metadata/* r,

  profile gpg flags=(attach_disconnected,mediate_deleted,complain) {
    include <abstractions/base>
    include <abstractions/consoles>

    capability dac_read_search,

    @{bin}/gpg{,2}    mr,
    @{bin}/gpgconf    mr,
    @{bin}/gpgsm      mr,
    @{bin}/gpg-agent  rix,

    @{HOME}/@{XDG_GPG_DIR}/*.conf r,

    owner @{tmp}/ostree-gpg-@{rand6}/ rw,
    owner @{tmp}/ostree-gpg-@{rand6}/** rwkl -> /tmp/ostree-gpg-@{rand6}/**,

    owner @{PROC}/@{pid}/fd/ r,

    include if exists <local/flatpak_gpg>
  }

  profile fusermount flags=(attach_disconnected,mediate_deleted,complain) {
    include <abstractions/base>
    include <abstractions/app/fusermount>

    capability setuid,

    mount fstype=fuse.revokefs-fuse options=(rw, nosuid, nodev) -> /var/tmp/flatpak-cache-*/*/,
    umount /var/tmp/flatpak-cache-*/*/,

    include if exists <local/flatpak_fusermount>
  }

  include if exists <local/flatpak>
}

# vim:syntax=apparmor
