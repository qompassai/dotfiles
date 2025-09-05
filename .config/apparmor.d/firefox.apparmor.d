# apparmor.d - Full set of apparmor profiles
# Copyright (C) 2015-2022 Mikhail Morfikov
# Copyright (C) 2021-2024 Alexandre Pujol <alexandre@pujol.io>
# SPDX-License-Identifier: GPL-2.0-only

abi <abi/4.0>,

include <tunables/global>

@{name} = firefox{,-esr,-bin}
@{lib_dirs} = @{lib}/firefox{,-esr,-beta,-devedition,-nightly} /opt/@{name}
@{config_dirs} = @{HOME}/.mozilla/
@{cache_dirs} = @{user_cache_dirs}/mozilla/

@{exec_path} = @{bin}/@{name} @{lib_dirs}/@{name}
profile firefox /{{,usr/}bin/firefox{,-esr,-bin},{,usr/}lib{,exec,32,64}/firefox{,-esr,-beta,-devedition,-nightly}/firefox{,-esr,-bin},opt/firefox{,-esr,-bin}/firefox{,-esr,-bin}}  flags=(attach_disconnected,complain) {
  include <abstractions/base>
  include <abstractions/app/firefox>
  include <abstractions/user-download-strict>
  include <abstractions/user-read-strict>

  signal send set=(term, kill) peer=firefox//&keepassxc-proxy,

  include <abstractions/bus/own-session>

  dbus bind bus=session name=org.mozilla.firefox{,.*},
  dbus receive bus=session path=/org/mozilla/firefox{,/**}
       interface=org.mozilla.firefox{,.*}
       peer=(name="@{busname}"),
  dbus send bus=session path=/org/mozilla/firefox{,/**}
       interface=org.mozilla.firefox{,.*}
       peer=(name="{@{busname},org.freedesktop.DBus}"),
  dbus (send receive) bus=session path=/org/mozilla/firefox{,/**}
       interface=org.freedesktop.DBus.Properties
       member={Get,GetAll,Set,PropertiesChanged}
       peer=(name="{@{busname},org.freedesktop.DBus}"),
  dbus receive bus=session path=/org/mozilla/firefox{,/**}
       interface=org.freedesktop.DBus.Introspectable
       member=Introspect
       peer=(name="@{busname}"),
  dbus receive bus=session path=/org/mozilla/firefox{,/**}
       interface=org.freedesktop.DBus.ObjectManager
       member=GetManagedObjects
       peer=(name="{@{busname},org.mozilla.firefox{,.*}}"),
  dbus send bus=session path=/org/mozilla/firefox{,/**}
       interface=org.freedesktop.DBus.ObjectManager
       member={InterfacesAdded,InterfacesRemoved}
       peer=(name="{@{busname},org.freedesktop.DBus}"),
  include <abstractions/bus/own-session>

  dbus bind bus=session name=org.mpris.MediaPlayer2.firefox{,.*},
  dbus receive bus=session path=/org/mpris/MediaPlayer2
       interface=org.mpris.MediaPlayer2.firefox{,.*}
       peer=(name="@{busname}"),
  dbus send bus=session path=/org/mpris/MediaPlayer2
       interface=org.mpris.MediaPlayer2.firefox{,.*}
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
       peer=(name="{@{busname},org.mpris.MediaPlayer2.firefox{,.*}}"),
  dbus send bus=session path=/org/mpris/MediaPlayer2
       interface=org.freedesktop.DBus.ObjectManager
       member={InterfacesAdded,InterfacesRemoved}
       peer=(name="{@{busname},org.freedesktop.DBus}"),

  @{exec_path} mrix,

  @{lib_dirs}/crashhelper rpx -> firefox//&firefox-crashhelper,
  @{lib_dirs}/glxtest     rpx -> firefox//&firefox-glxtest,
  @{lib_dirs}/vaapitest   rpx -> firefox//&firefox-vaapitest,

  @{lib}/@{multiarch}/qt5/plugins/kf5/org.kde.kwindowsystem.platforms/KF5WindowSystemKWaylandPlugin.so mr,
  @{lib}/@{multiarch}/qt5/plugins/kf5/org.kde.kwindowsystem.platforms/KF5WindowSystemX11Plugin.so mr,
  @{lib}/mozilla/plugins/ r,
  @{lib}/mozilla/plugins/*.so mr,

  # Desktop integration
  @{bin}/gnome-software                              rpx,
  @{bin}/kreadconfig{,5}                             rpx,
  @{bin}/plasma-browser-integration-host             rpx,
  @{bin}/speech-dispatcher                           rpx,
  @{bin}/update-mime-database                        rpx,
  @{lib}/gvfsd-metadata                              rpx,
  @{lib}/mozilla/kmozillahelper                     rpux,
  @{open_path}                                       rpx -> child-open,

  # Common extensions
  /opt/net.downloadhelper.coapp/bin/net.downloadhelper.coapp*  rpx,
  @{bin}/browserpass         rpx,
  @{bin}/keepassxc-proxy     rpx -> firefox//&keepassxc-proxy,

  owner @{user_config_dirs}/gtk-{3,4}.0/assets/*.svg r,
  owner @{user_config_dirs}/ibus/bus/ r,
  owner @{user_config_dirs}/ibus/bus/@{hex32}-unix-{,wayland-}@{int} r,
  owner @{user_config_dirs}/kioslaverc r,
  owner @{user_config_dirs}/mimeapps.list{,.@{rand6}} rw,

  owner @{user_share_dirs}/applications/userapp-Firefox-@{rand6}.desktop{,.@{rand6}} rw,
  owner @{user_share_dirs}/mime/packages/user-extension-{htm,html,xht,xhtml,shtml}.xml rw,
  owner @{user_share_dirs}/mime/packages/user-extension-{htm,html,xht,xhtml,shtml}.xml.* rw,

  owner @{tmp}/.xfsm-ICE-@{rand6} rw,
  owner @{tmp}/@{rand8}.* rw,  # file downloads (to anywhere)
  owner @{tmp}/@{uuid}.zip{,.tmp} rw,
  owner @{tmp}/Mozilla@{uuid}-cachePurge-{@{hex15},@{hex16}} rwk,
  owner @{tmp}/mozilla* rw,
  owner @{tmp}/mozilla*/ rw,
  owner @{tmp}/mozilla*/* rwk,
  owner @{tmp}/Mozilla\{@{uuid}\}-cachePurge-{@{hex15},@{hex16}} rwk,
  owner @{tmp}/MozillaBackgroundTask-{@{hex15},@{hex16}}-removeDirectory/.parentlock k,
  owner @{tmp}/MozillaBackgroundTask-{@{hex15},@{hex16}}-removeDirectory/{**,} rw,
  owner @{tmp}/Mozillato-be-removed-cachePurge-{@{hex15},@{hex16}} rwk,

  owner @{run}/user/@{uid}/org.keepassxc.KeePassXC.BrowsrServer w,

  # Silencer
  deny @{lib_dirs}/** w,

  include if exists <local/firefox>
}

# vim:syntax=apparmor
