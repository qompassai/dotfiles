<!-- /qompassai/dotfiles/.config/wireplumber/README.md -->
<!-- Qompass AI WirePlumber Documentation -->
<!-- Copyright (C) 2026 Qompass AI, All rights reserved -->
<!-- ---------------------------------------- -->

<div align="center">

# WirePlumber SPA Libraries Configuration

A comprehensive guide to SPA (Simple Plugin API) libraries for WirePlumber audio/video session management.

***

  <details style="display: inline-block; text-align: left; max-width: 600px; width: 100%;">
<summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;">
    <div class="icon-row" style="display: flex; align-items: center; gap: 6px;">
      <img src="https://raw.githubusercontent.com/qompassai/svg/refs/heads/main/assets/icons/audio/alsa.svg"
           alt="alsa" width="60" height="60" title="ALSA" />
    </div>
    <strong>ALSA (Advanced Linux Sound Architecture)</strong>
  </summary>
  <blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
    <p><strong>Purpose:</strong> Native Linux kernel audio interface providing PCM (Pulse Code Modulation) playback and capture.</p>
    <p><strong>Configuration:</strong></p>
    <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```jsonc
context.spa-libs = {
  api.alsa.* = alsa/libspa-alsa
}
```

</div> <p><strong>Installation:</strong></p> <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```bash

# Arch Linux

sudo pacman -S pipewire alsa-lib

# Verify installation

ls /usr/lib/spa-0.2/alsa/libspa-alsa.so
spa-inspect /usr/lib/spa-0.2/alsa/libspa-alsa.so
```

</div> <p><strong>Factory Names:</strong> <code>api.alsa.enum.udev</code>, <code>api.alsa.pcm.sink</code>, <code>api.alsa.pcm.source</code></p> <p> <a href="https://docs.pipewire.org/page_spa_plugins.html">ALSA SPA Reference</a> </p> </blockquote> </details> <details style="display: inline-block; text-align: left; max-width: 600px; width: 100%;"> <summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;"> <div class="icon-row" style="display: flex; align-items: center; gap: 6px;"> <img src="https://raw.githubusercontent.com/qompassai/svg/refs/heads/main/assets/icons/audio/bluetooth.svg" alt="bluez5" width="60" height="60" title="BlueZ5" /> </div> <strong>BlueZ5 (Bluetooth Audio)</strong> </summary> <blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"> <p><strong>Purpose:</strong> Bluetooth audio device support with A2DP, HSP, HFP codec support.</p> <p><strong>Configuration:</strong></p> <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```json
context.spa-libs = {
api.bluez5.\* = bluez5/libspa-bluez5
}
```

</div> <p><strong>Installation:</strong></p> <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```bash

# Arch Linux

sudo pacman -S pipewire-pulse bluez bluez-libs

# Enable Bluetooth service

systemctl --user enable --now bluetooth.service

# Verify installation

ls /usr/lib/spa-0.2/bluez5/libspa-bluez5.so
```

</div> <p><strong>Factory Names:</strong> <code>api.bluez5.enum.dbus</code>, <code>api.bluez5.midi.enum</code></p> <p> <a href="https://wiki.archlinux.org/title/WirePlumber#Bluetooth">BlueZ5 WirePlumber Reference</a> </p> </blockquote> </details> <details style="display: inline-block; text-align: left; max-width: 600px; width: 100%;"> <summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;"> <div class="icon-row" style="display: flex; align-items: center; gap: 6px;"> <img src="https://raw.githubusercontent.com/qompassai/svg/refs/heads/main/assets/icons/video/camera.svg" alt="libcamera" width="60" height="60" title="libcamera" /> </div> <strong>libcamera (Modern Camera API)</strong> </summary> <blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"> <p><strong>Purpose:</strong> Modern Linux camera framework supporting complex camera hardware with advanced features.</p> <p><strong>Configuration:</strong></p> <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```json
context.spa-libs = {
api.libcamera.\* = libcamera/libspa-libcamera
}
```

</div> <p><strong>Installation:</strong></p> <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

bash

# Arch Linux

sudo pacman -S libcamera pipewire

# Verify installation

ls /usr/lib/spa-0.2/libcamera/libspa-libcamera.so

</div> <p><strong>Factory Names:</strong> <code>api.libcamera.enum.client</code>, <code>api.libcamera.source</code></p> <p> <a href="https://libcamera.org/">libcamera Official Site</a> </p> </blockquote> </details> <details style="display: inline-block; text-align: left; max-width: 600px; width: 100%;"> <summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;"> <div class="icon-row" style="display: flex; align-items: center; gap: 6px;"> <img src="https://raw.githubusercontent.com/qompassai/svg/refs/heads/main/assets/icons/video/v4l2.svg" alt="v4l2" width="60" height="60" title="V4L2" /> </div> <strong>V4L2 (Video4Linux2)</strong> </summary> <blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"> <p><strong>Purpose:</strong> Legacy video capture API for webcams and video devices.</p> <p><strong>Configuration:</strong></p> <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```jsonc
context.spa-libs = {
api.v4l2.\* = v4l2/libspa-v4l2
}
```

</div> <p><strong>Installation:</strong></p> <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

bash

# Arch Linux (usually included by default)

sudo pacman -S v4l-utils pipewire

# List video devices

v4l2-ctl --list-devices

# Verify installation

ls /usr/lib/spa-0.2/v4l2/libspa-v4l2.so

</div> <p><strong>Factory Names:</strong> <code>api.v4l2.source</code>, <code>api.v4l2.enum.udev</code></p> <p> <a href="https://www.kernel.org/doc/html/latest/userspace-api/media/v4l/v4l2.html">V4L2 Kernel Documentation</a> </p> </blockquote> </details> <details style="display: inline-block; text-align: left; max-width: 600px; width: 100%;"> <summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;"> <div class="icon-row" style="display: flex; align-items: center; gap: 6px;"> <img src="https://raw.githubusercontent.com/qompassai/svg/refs/heads/main/assets/icons/graphics/vulkan.svg" alt="vulkan" width="60" height="60" title="Vulkan" /> </div> <strong>Vulkan (Graphics Compute API)</strong> </summary> <blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"> <p><strong>Purpose:</strong> GPU-accelerated video/image processing using Vulkan compute shaders.</p> <p><strong>Configuration:</strong></p> <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

lua
context.spa-libs = {
api.vulkan.\* = vulkan/libspa-vulkan
}

</div> <p><strong>Installation:</strong></p> <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

bash

# Arch Linux

sudo pacman -S vulkan-icd-loader vulkan-tools pipewire

# Verify Vulkan support

vulkaninfo | head -20

# Verify installation

ls /usr/lib/spa-0.2/vulkan/libspa-vulkan.so

</div> <p><strong>Factory Names:</strong> <code>api.vulkan.compute.source</code></p> <p> <a href="https://www.vulkan.org/">Vulkan Official Site</a> </p> </blockquote> </details> <details style="display: inline-block; text-align: left; max-width: 600px; width: 100%;"> <summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;"> <div class="icon-row" style="display: flex; align-items: center; gap: 6px;"> <img src="https://raw.githubusercontent.com/qompassai/svg/refs/heads/main/assets/icons/audio/aec.svg" alt="aec" width="60" height="60" title="AEC" /> </div> <strong>AEC (Acoustic Echo Cancellation)</strong> </summary> <blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"> <p><strong>Purpose:</strong> Real-time acoustic echo cancellation for voice calls and conferencing.</p> <p><strong>Configuration:</strong></p> <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

lua
context.spa-libs = {
audio.aec.\* = aec/libspa-aec
}

</div> <p><strong>Installation:</strong></p> <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

bash

# Arch Linux (requires WebRTC audio processing)

sudo pacman -S pipewire webrtc-audio-processing

# Verify installation

ls /usr/lib/spa-0.2/aec/libspa-aec.so
spa-inspect /usr/lib/spa-0.2/aec/libspa-aec.so

</div> <p><strong>Factory Names:</strong> <code>audio.aec.webrtc</code></p> <p> <a href="https://docs.pipewire.org/page_module_echo_cancel.html">Echo Cancellation Module Documentation</a> </p> </blockquote> </details> <details style="display: inline-block; text-align: left; max-width: 600px; width: 100%;"> <summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;"> <div class="icon-row" style="display: flex; align-items: center; gap: 6px;"> <img src="https://raw.githubusercontent.com/qompassai/svg/refs/heads/main/assets/icons/audio/convert.svg" alt="audioconvert" width="60" height="60" title="Audio Convert" /> </div> <strong>Audio Convert (Format Conversion)</strong> </summary> <blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"> <p><strong>Purpose:</strong> Audio format, sample rate, and channel conversion with resampling.</p> <p><strong>Configuration:</strong></p> <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

lua
context.spa-libs = {
audio.convert.\* = audioconvert/libspa-audioconvert
}

</div> <p><strong>Installation:</strong></p> <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

bash

# Arch Linux (core component)

sudo pacman -S pipewire

# Verify installation

ls /usr/lib/spa-0.2/audioconvert/libspa-audioconvert.so

</div> <p><strong>Factory Names:</strong> <code>audio.convert</code>, <code>audio.resample</code>, <code>audio.channelmix</code></p> <p> <a href="https://docs.pipewire.org/page_spa_plugins.html">Audio Convert SPA Reference</a> </p> </blockquote> </details> <details style="display: inline-block; text-align: left; max-width: 600px; width: 100%;"> <summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;"> <div class="icon-row" style="display: flex; align-items: center; gap: 6px;"> <img src="https://raw.githubusercontent.com/qompassai/svg/refs/heads/main/assets/icons/audio/mixer.svg" alt="audiomixer" width="60" height="60" title="Audio Mixer" /> </div> <strong>Audio Mixer (Stream Mixing)</strong> </summary> <blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"> <p><strong>Purpose:</strong> Combines multiple audio input streams into a single output stream.</p> <p><strong>Configuration:</strong></p> <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```jsonc
context.spa-libs = {
audio.mixer.\* = audiomixer/libspa-audiomixer
}
```

```
```

</div> <p><strong>Installation:</strong></p> <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```bash
sudo pacman -S pipewire

ls /usr/lib/spa-0.2/audiomixer/libspa-audiomixer.so
```

</div> <p><strong>Factory Names:</strong> <code>audio.mixer.dsp</code></p> <p> <a href="https://docs.pipewire.org/page_spa_plugins.html">Audio Mixer SPA Reference</a> </p> </blockquote> </details> <details style="display: inline-block; text-align: left; max-width: 600px; width: 100%;"> <summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;"> <div class="icon-row" style="display: flex; align-items: center; gap: 6px;"> <img src="https://raw.githubusercontent.com/qompassai/svg/refs/heads/main/assets/icons/system/control.svg" alt="control" width="60" height="60" title="Control" /> </div> <strong>Control (Device Control)</strong> </summary> <blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"> <p><strong>Purpose:</strong> Control signal mixer for device control streams.</p> <p><strong>Configuration:</strong></p> <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```jsonc
context.spa-libs = {
control.\* = control/libspa-control
}
```

</div> <p><strong>Installation:</strong></p> <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

bash

# Arch Linux (core component)

sudo pacman -S pipewire

# Verify installation

ls /usr/lib/spa-0.2/control/libspa-control.so

</div> <p><strong>Factory Names:</strong> <code>control.mixer</code></p> <p> <a href="https://docs.pipewire.org/page_spa_plugins.html">Control SPA Reference</a> </p> </blockquote> </details> <details style="display: inline-block; text-align: left; max-width: 600px; width: 100%;"> <summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;"> <div class="icon-row" style="display: flex; align-items: center; gap: 6px;"> <img src="https://raw.githubusercontent.com/qompassai/svg/refs/heads/main/assets/icons/system/support.svg" alt="support" width="60" height="60" title="Support" /> </div> <strong>Support (Core Infrastructure)</strong> </summary> <blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"> <p><strong>Purpose:</strong> Essential core support including CPU detection, logging, event loops, and system utilities.</p> <p><strong>Configuration:</strong></p> <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```jsonc
context.spa-libs = {
support.\* = support/libspa-support
}
```

</div> <p><strong>Installation:</strong></p> <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```bash

# Arch Linux (core component, always required)

sudo pacman -S pipewire

# Verify installation

ls /usr/lib/spa-0.2/support/libspa-support.so
spa-inspect /usr/lib/spa-0.2/support/libspa-support.so
```

</div> <p><strong>Factory Names:</strong> <code>support.cpu</code>, <code>support.logger</code>, <code>support.loop</code>, <code>support.system</code></p> <p> <a href="https://docs.pipewire.org/page_spa_plugins.html">Support SPA Reference</a> </p> </blockquote> </details> <details style="display: inline-block; text-align: left; max-width: 600px; width: 100%;"> <summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;"> <div class="icon-row" style="display: flex; align-items: center; gap: 6px;"> <img src="https://raw.githubusercontent.com/qompassai/svg/refs/heads/main/assets/icons/video/convert.svg" alt="videoconvert" width="60" height="60" title="Video Convert" /> </div> <strong>Video Convert (Video Format Conversion)</strong> </summary> <blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"> <p><strong>Purpose:</strong> Video format, resolution, and colorspace conversion.</p> <p><strong>Configuration:</strong></p> <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

lua
context.spa-libs = {
video.convert.\* = videoconvert/libspa-videoconvert
}

</div> <p><strong>Installation:</strong></p> <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```bash

# Arch Linux (core component)

sudo pacman -S pipewire

# Verify installation

ls /usr/lib/spa-0.2/videoconvert/libspa-videoconvert.so
```

</div> <p><strong>Factory Names:</strong> <code>video.convert</code>, <code>video.scale</code></p> <p> <a href="https://docs.pipewire.org/page_spa_plugins.html">Video Convert SPA Reference</a> </p> </blockquote> </details>
