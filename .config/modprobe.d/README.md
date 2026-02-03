<!-- /qompassai/arch/etc/modprobe.d/README.md -->
<!-- Qompass AI Modprobe.d Docs -->
<!-- Copyright (C) 2025 Qompass AI, All rights reserved -->
<!-- ---------------------------------------- -->

<h1 align="center">Dynamic Kernel Module Support (DKMS) Modprobe.d Config</h1>

<div align="center" style="margin-top: 16px;">

  <a href="https://wiki.archlinux.org/title/Kernel_module">
    Kernel modules (ArchWiki)
  </a> ·

  <a href="https://wiki.archlinux.org/title/Sound_system">
    Audio / sound system
  </a> ·

  <a href="https://wiki.archlinux.org/title/Kernel_module#Blacklisting">
    Blacklisting modules
  </a> ·

  <a href="https://wiki.archlinux.org/title/Thunderbolt">
    Thunderbolt devices
  </a> ·

  <a href="https://wiki.archlinux.org/title/Intel_graphics">
    Intel graphics
  </a> ·

  <a href="https://wiki.archlinux.org/title/Network_configuration">
    Network configuration
  </a> ·

  <a href="https://wiki.archlinux.org/title/NVIDIA">
    NVIDIA drivers
  </a> ·

  <a href="https://wiki.archlinux.org/title/Webcam_setup">
    Webcam / v4l2loopback
  </a>

 <div align="center" style="margin: 10px 0;">
  DKMS modules script:
  <a href="https://github.com/qompassai/dotfiles/blob/main/.config/dkms/dkms.sh">
    qompassai/dotfiles/.config/dkms/dkms.sh
  </a>
</div>
  <details>
<summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0;"><strong>DKMS Packages</strong></summary>
<blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">

- [acpi_call-dkms](https://aur.archlinux.org/packages/acpi_call-dkms)
- [akvcam-dkms](https://aur.archlinux.org/packages/akvcam-dkms)
- [boost174](https://aur.archlinux.org/packages/boost174)
- [blackmagic](https://aur.archlinux.org/packages/blackmagic)
- [broadcom-wl-dkms](https://aur.archlinux.org/packages/broadcom-wl-dkms)
- [chipsec-dkms-git](https://aur.archlinux.org/packages/chipsec-dkms-git)
- [corefreq-dkms](https://aur.archlinux.org/packages/corefreq-dkms)
- [cryptodev-linux-dkms](https://aur.archlinux.org/packages/cryptodev-linux-dkms)
- [cuda-boost-bypass](https://aur.archlinux.org/packages/cuda-boost-bypass)
- [dm-sflc-dkms](https://aur.archlinux.org/packages/dm-sflc-dkms)
- [drbd-dkms](https://aur.archlinux.org/packages/drbd-dkms)
- [droidcam-dkms](https://aur.archlinux.org/packages/droidcam-dkms)
- [dstep](https://aur.archlinux.org/packages/dstep)
- [exanic-dkms](https://aur.archlinux.org/packages/exanic-dkms)
- [fortify-headers](https://aur.archlinux.org/packages/fortify-headers)
- [gasket-dkms-git](https://aur.archlinux.org/packages/gasket-dkms-git)
- [haxm-dkms-git](https://aur.archlinux.org/packages/haxm-dkms-git)
- [hp_vendor-dkms](https://aur.archlinux.org/packages/hp_vendor-dkms)
- [ibdump](https://aur.archlinux.org/packages/ibdump)
- [kernel-mft-dkms](https://aur.archlinux.org/packages/kernel-mft-dkms)
- [kmon](https://aur.archlinux.org/packages/kmon)
- [lkrg-dkms](https://aur.archlinux.org/packages/lkrg-dkms)
- [linux-gpib-dkms](https://aur.archlinux.org/packages/linux-gpib-dkms)
- [looking-glass-module-dkms](https://aur.archlinux.org/packages/looking-glass-module-dkms)
- [mimic-bpf-dkms](https://aur.archlinux.org/packages/mimic-bpf-dkms)
- [mstflint](https://aur.archlinux.org/packages/mstflint)
- [mtgpu-dkms](https://aur.archlinux.org/packages/mtgpu-dkms)
- [netatop-dkms](https://aur.archlinux.org/packages/netatop-dkms)
- [netfilter-fullconenat-dkms-git](https://aur.archlinux.org/packages/netfilter-fullconenat-dkms-git)
- [nvidia-fs-dkms](https://aur.archlinux.org/packages/nvidia-fs-dkms)
- [nvidia-open-dkms](https://aur.archlinux.org/packages/nvidia-open-dkms)
- [nullfsvfs-dkms](https://aur.archlinux.org/packages/nullfsvfs-dkms)
- [msi-psu-dkms](https://aur.archlinux.org/packages/msi-psu-dkms)
- [nvidia-mft](https://aur.archlinux.org/packages/nvidia-mft)
- [ovpn-dco-dkms](https://aur.archlinux.org/packages/ovpn-dco-dkms)
- [pat-dealloc-dkms](https://aur.archlinux.org/packages/pat-dealloc-dkms)
- [pfring-dkms](https://aur.archlinux.org/packages/pfring-dkms)
- [r8125-dkms](https://aur.archlinux.org/packages/r8125-dkms)
- [rapiddisk-dkms](https://aur.archlinux.org/packages/rapiddisk-dkms)
- [rtpengine-kernel-dkms](https://aur.archlinux.org/packages/rtpengine-kernel-dkms)
- [rtw89-dkms-git](https://aur.archlinux.org/packages/rtw89-dkms-git)
- [rtw89bt-dkms-git](https://aur.archlinux.org/packages/rtw89bt-dkms-git)
- [scap-dkms](https://aur.archlinux.org/packages/scap-dkms)
- [scst-dkms](https://aur.archlinux.org/packages/scst-dkms)
- [smartcam-dkms](https://aur.archlinux.org/packages/smartcam-dkms)
- [snd-hdspe-dkms](https://aur.archlinux.org/packages/snd-hdspe-dkms)
- [snd-pcsp-dkms](https://aur.archlinux.org/packages/snd-pcsp-dkms)
- [snd-usb-audio-fasttrack-dkms](https://aur.archlinux.org/packages/snd-usb-audio-fasttrack-dkms)
- [tcp-brutal-dkms](https://aur.archlinux.org/packages/tcp-brutal-dkms)
- [tyton-dkms-git](https://aur.archlinux.org/packages/tyton-dkms-git)
- [util-linux-libs-aes](https://aur.archlinux.org/packages/util-linux-libs-aes)
- [virtualbox-host-dkms](https://archlinux.org/packages/?name=virtualbox-host-dkms)
- [vhba-module-dkms](https://aur.archlinux.org/packages/vhba-module-dkms)
- [vtunerc-dkms](https://aur.archlinux.org/packages/vtunerc-dkms)
- [v4l2loopback-dkms](https://aur.archlinux.org/packages/v4l2loopback-dkms)
- [v4l2loopback-dc-dkms](https://aur.archlinux.org/packages/v4l2loopback-dc-dkms)
- [winesync-dkms](https://aur.archlinux.org/packages/winesync-dkms)
- [winesync-header](https://aur.archlinux.org/packages/winesync-header)
- [wireguard-dkms](https://aur.archlinux.org/packages/wireguard-dkms)
- [xtables-addons-dkms](https://aur.archlinux.org/packages/xtables-addons-dkms)
- [xt_wgobfs-dkms](https://aur.archlinux.org/packages/xt_wgobfs-dkms)
- [zoom-l8-dkms](https://aur.archlinux.org/packages/zoom-l8-dkms)
- [zfs-dkms](https://aur.archlinux.org/packages/zfs-dkms)

  </blockquote>
</details>


</div>
  <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">
    <table>
      <thead>
        <tr>
          <th style="text-align:center;">Config File</th>
          <th style="text-align:center;">Purpose</th>
          <th style="text-align:center;">Modules</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>audio.conf</td>
          <td>Vendor agnostic audio (pipewire, alsa)</td>
          <td>snd_hda_intel, snd-usb-audio</td>
        </tr>
        <tr>
          <td>blacklist.conf</td>
          <td>Disable modules (advanced)</td>
          <td>airspy, dvb_usb_rtl28xxu, hackrf, nouveau, r8169, rtw89*, rtw_*, rtl*, rtwcore</td>
        </tr>
        <tr>
          <td>devices.conf</td>
          <td>Device specifics (Thunderbolt, USB, HDMI, NVME)</td>
          <td>dm_mod, loop, mmc_core, overlay, rtsx_pci, thunderbolt, zram</td>
        </tr>
        <tr>
          <td>drm.conf</td>
          <td>Digital Rights Management (DRM) for displays</td>
          <td>drm_display_helper, gpu_sched</td>
        </tr>
        <tr>
          <td>encrypt.conf</td>
          <td>Cryptography/Encryption protocols</td>
          <td>cryptodev, lkrg</td>
        </tr>
        <tr>
          <td>intel.conf</td>
          <td>Intel specifics</td>
          <td>i915, kvm, kvm_intel, snd_sof_intel_hda, soundwire*, vfio_pci, xe</td>
        </tr>
        <tr>
          <td>network.conf</td>
          <td>Ethernet, Wifi, Bluetooth</td>
          <td>bluetooth, btusb, cfg80211, iwlwifi, mac80211, mlx4_(core, en, ib), ib_(ipoib, iser, isert, srp, srpt, set, qib), ip_(ipoib, set), nf_conntrack, r8125, rfcomm, rtw89core_git, rtw89pci_git, rtw89_usb_git</td>
        </tr>
        <tr>
          <td>nvidia.conf</td>
          <td>NVIDIA specific</td>
          <td>nvidia, nvidia_drm, nvidia_modeset, nvidia_uvm</td>
        </tr>
        <tr>
          <td>video.conf</td>
          <td>Video specific (v4l2loopback, uvc, blackmagic)</td>
          <td>blackmagic, cec, uvcvideo, v4l2loopback, v4l2loopback_dc</td>
        </tr>
      </tbody>
    </table>
  </div>


