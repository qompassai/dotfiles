<!-- /qompassai/Dotfiles/.config/README.md -->
<!-- Qompass AI Dotfiles Config Docs -->
<!-- Copyright (C) 2026 Qompass AI, All rights reserved -->
<!-- ---------------------------------------- -->

<div align="center">

<img src="https://raw.githubusercontent.com/qompassai/svg/refs/heads/main/assets/qompass/qompass.svg" alt="Qompass AI" width="120" height="120" />

# Qompass AI Dotfiles

**XDG-compliant configuration files for the Qompass AI development environment**

![Arch Linux](https://img.shields.io/badge/Arch_Linux-1793D1?style=for-the-badge&logo=arch-linux&logoColor=white)
![Hyprland](https://img.shields.io/badge/Hyprland-58E1FF?style=for-the-badge&logo=hyprland&logoColor=black)
![License](https://img.shields.io/badge/License-GQL-667eea?style=for-the-badge)

</div>

---

## Overview

All configs follow X Desktop Group (XDG) convention `$XDG_CONFIG_HOME` (`~/.config`) 

---

<div align="center">

<details>
<summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;">
  <strong>A — Audio, Automation & Access</strong>
</summary>
<blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
  <ul>
  <li><a href=".config/abuild">abuild</a> — Arch build</li>
  <li><a href=".config/acme-redirect.d">acme-redirect.d</a> — ACME DNS Redirect</li>
    <li><a href=".config/alsa">alsa</a> — ALSA audio device configuration</li>
    <li><a href=".config/alsacontrol">alsacontrol</a> — ALSA mixer control</li>
  <li><a href=".config/alsacontrol">alsacontrol</a> — Virtual Reality</li>
    <li><a href=".config/amsynth">amsynth</a> — Software synthesizer</li>
    <li><a href=".config/ansible-bundler">ansible-bundler</a> — Ansible automation bundler</li>
   <li><a href=".config/amsynth">amsynth</a> — Java ant</li>
    <li><a href=".config/apparmor">apparmor</a> — AppArmor MAC security profiles</li>
    <li><a href=".config/appimagelauncher">appimagelauncher</a> — AppImage integration</li>
    <li><a href=".config/aria2">aria2</a> — Lightweight download utility</li>
    <li><a href=".config/arrpc">arrpc</a> — Discord Rich Presence bridge</li>
    <li><a href=".config/arti">arti</a> — Rust Tor implementation</li>
    <li><a href=".config/astro">astro</a> — Astronvim configuration</li>
    <li><a href=".config/audacity">audacity</a> — Audio editor</li>
  </ul>
<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

</div>
</blockquote>
</details>
<details>
<summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;">
  <strong>B </strong>
</summary>
<blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
  <ul>
    <li><a href=".config/bacon">bacon</a> — Background Rust code checker</li>
    <li><a href=".config/bash">bash</a> — Bash shell configuration</li>
    <li><a href=".config/basedpyright">basedpyright</a> — Python type checker (fork)</li>
    <li><a href=".config/bemenu">bemenu</a> — Dynamic menu library</li>
    <li><a href=".config/biome">biome</a> — JS/TS/JSON toolchain</li>
    <li><a href=".config/bluetooth">bluetooth</a> — BlueZ Bluetooth daemon config</li>
    <li><a href=".config/bob">bob</a> — Neovim version manager</li>
    <li><a href=".config/btop">btop</a> — Resource monitor</li>
    <li><a href=".config/burp">burp</a> — Network backup client</li>
    <li><a href=".config/byobu">byobu</a> — Terminal multiplexer</li>
  </ul>
<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```bash
export BTOP_CONFIG="$XDG_CONFIG_HOME/btop/btop.conf"
```

</div>
</blockquote>
</details>

<details>
<summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;">
  <strong>C</strong>
</summary>
<blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
  <ul>
    <li><a href=".config/caddy">caddy</a> — Caddy web server</li>
    <li><a href=".config/cargo">cargo</a> — Rust package manager</li>
    <li><a href=".config/cava">cava</a> — Console audio visualizer</li>
    <li><a href=".config/clamav">clamav</a> — Antivirus engine</li>
    <li><a href=".config/containers">containers</a> — Podman/Docker container config</li>
    <li><a href=".config/couchdb">couchdb</a> — CouchDB document store</li>
    <li><a href=".config/cuda">cuda</a> — NVIDIA CUDA toolkit config</li>
  </ul>
<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```bash
export CARGO_HOME="$XDG_DATA_HOME/cargo"
export RUSTUP_HOME="$XDG_DATA_HOME/rustup"
```

</div>
</blockquote>
</details>

<details>
<summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;">
  <strong>D</strong>
</summary>
<blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
  <ul>
    <li><a href=".config/dbeaver">dbeaver</a> — Universal database tool</li>
    <li><a href=".config/dbus-1">dbus-1</a> — D-Bus system/session bus config</li>
    <li><a href=".config/discord-irc">discord-irc</a> — Discord ↔ IRC bridge</li>
    <li><a href=".config/discordo">discordo</a> — Terminal Discord client</li>
    <li><a href=".config/docker">docker</a> — Docker container engine</li>
    <li><a href=".config/dnscrypt-proxy">dnscrypt-proxy</a> — Encrypted DNS proxy</li>
    <li><a href=".config/dnsmasq">dnsmasq</a> — Lightweight DNS/DHCP server</li>
    <li><a href=".config/dunst">dunst</a> — Notification daemon</li>
    <li><a href=".config/dxvk">dxvk</a> — DirectX-to-Vulkan translation</li>
  </ul>
<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```bash
sudo cp /etc/dnscrypt-proxy/dnscrypt-proxy.toml   "$XDG_CONFIG_HOME/dnscrypt-proxy/dnscrypt-proxy.toml"
```

</div>
</blockquote>
</details>

<details>
<summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;">
  <strong>E — Editors, Environment & Effects</strong>
</summary>
<blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
  <ul>
    <li><a href=".config/easyeffects">easyeffects</a> — PipeWire audio effects</li>
    <li><a href=".config/editorconfig">editorconfig</a> — Cross-editor coding style</li>
    <li><a href=".config/efm-langserver">efm-langserver</a> — General LSP for linters</li>
    <li><a href=".config/environment.d">environment.d</a> — systemd user environment</li>
    <li><a href=".config/eslint">eslint</a> — JavaScript/TypeScript linter</li>
  </ul>
<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```bash
cat "$XDG_CONFIG_HOME/environment.d/xdg.conf"
```

</div>
</blockquote>
</details>

<details>
<summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;">
  <strong>F — Fonts, Fish & File Managers</strong>
</summary>
<blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
  <ul>
    <li><a href=".config/fastfetch">fastfetch</a> — Fast system info fetcher</li>
    <li><a href=".config/fcitx5">fcitx5</a> — Input method framework</li>
    <li><a href=".config/ffmpeg">ffmpeg</a> — Multimedia framework config</li>
    <li><a href=".config/firejail">firejail</a> — Security sandbox</li>
    <li><a href=".config/fish">fish</a> — Fish shell configuration</li>
    <li><a href=".config/fontconfig">fontconfig</a> — Font rendering config</li>
    <li><a href=".config/foot">foot</a> — Fast Wayland terminal</li>
    <li><a href=".config/fuzzel">fuzzel</a> — Application launcher (Wayland)</li>
    <li><a href=".config/fwupd">fwupd</a> — Firmware update daemon</li>
  </ul>
<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```bash
"$XDG_CONFIG_HOME/fish/config.fish"
```

</div>
</blockquote>
</details>

<details>
<summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;">
  <strong>G — Git, GTK & GPU</strong>
</summary>
<blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
  <ul>
    <li><a href=".config/gamescope">gamescope</a> — Steam session compositor</li>
    <li><a href=".config/git">git</a> — Git VCS config and hooks</li>
    <li><a href=".config/githooks">githooks</a> — Global git hook scripts</li>
    <li><a href=".config/github">github</a> — GitHub CLI and token config</li>
    <li><a href=".config/gnupg">gnupg</a> — GPG keyring config</li>
    <li><a href=".config/godot">godot</a> — Godot game engine</li>
    <li><a href=".config/greetd">greetd</a> — Minimal display manager</li>
    <li><a href=".config/gtk-2.0">gtk-2.0</a> / <a href=".config/gtk-3.0">gtk-3.0</a> / <a href=".config/gtk-4.0">gtk-4.0</a> — GTK theming</li>
  </ul>
<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```bash
export GIT_CONFIG_GLOBAL="$XDG_CONFIG_HOME/git/config"
```

</div>
</blockquote>
</details>


<details>
<summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;">
  <strong>H</strong>
</summary>
<blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
  <ul>
    <li><a href=".config/haproxy">haproxy</a> — High-availability load balancer</li>
    <li><a href=".config/hostapd">hostapd</a> — IEEE 802.11 AP daemon</li>
    <li><a href=".config/hotplug">hotplug</a> — Device hotplug rules</li>
    <li><a href=".config/hyprmon">hyprmon</a> — Hyprland Config</li>
    <li><a href=".config/hyprmon">hyprmon</a> — Hyprland monitor management</li>
  </ul>
<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```bash
"$XDG_CONFIG_HOME/hypr/hyprland.conf"
```

</div>
</blockquote>
</details>

<details>
<summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;">
  <strong>I</strong>
</summary>
<blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
  <ul>
    <li><a href=".config/input">input</a> — libinput device configuration</li>
    <li><a href=".config/input-remapper">input-remapper</a> — Key/button remapping</li>
    <li><a href=".config/inputplumber">inputplumber</a> — Unified input management</li>
    <li><a href=".config/inspircd">inspircd</a> — IRC server daemon</li>
    <li><a href=".config/intel">intel</a> — Intel GPU config</li>
    <li><a href=".config/ipython">ipython</a> — Interactive Python config</li>
    <li><a href=".config/irssi">irssi</a> — Terminal IRC client</li>
    <li><a href=".config/iwd">iwd</a> — Intel wireless daemon</li>
  </ul>
<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```bash
export IWD_CONF_DIR="$XDG_CONFIG_HOME/iwd"
```

</div>
</blockquote>
</details>

<details>
<summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;">
  <strong>J-K</strong>
</summary>
<blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
  <ul>
    <li><a href=".config/jellyfin">jellyfin</a> — Media server</li>
    <li><a href=".config/jj">jj</a> — Jujutsu VCS config</li>
    <li><a href=".config/julia">julia</a> — Julia language config</li>
    <li><a href=".config/jupyter">jupyter</a> — Jupyter notebooks config</li>
    <li><a href=".config/khal">khal</a> — Terminal calendar client</li>
    <li><a href=".config/kitty">kitty</a> — GPU-accelerated terminal</li>
    <li><a href=".config/krita">krita</a> — Digital painting studio</li>
    <li><a href=".config/kvantum">kvantum</a> — Qt5/Qt6 SVG theme engine</li>
  </ul>
</blockquote>
</details>

<details>
<summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;">
  <strong>L — Lua, LSP & Logging</strong>
</summary>
<blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
  <ul>
    <li><a href=".config/libao">libao</a> — Audio output library config</li>
    <li><a href=".config/llm">llm</a> — LLM CLI tool config</li>
    <li><a href=".config/loki">loki</a> — Log aggregation (Grafana Loki)</li>
    <li><a href=".config/lua">lua</a> — Lua interpreter config</li>
    <li><a href=".config/luacheck">luacheck</a> — Lua static analyzer</li>
    <li><a href=".config/luarocks">luarocks</a> — Lua package manager</li>
    <li><a href=".config/lynx">lynx</a> — Terminal web browser</li>
  </ul>
<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```bash
export LUAROCKS_CONFIG="$XDG_CONFIG_HOME/luarocks/config.lua"
```

</div>
</blockquote>
</details>

<details>
<summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;">
  <strong>M — Mail, Monitoring & Media</strong>
</summary>
<blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
  <ul>
    <li><a href=".config/mako">mako</a> — Lightweight Wayland notification daemon</li>
    <li><a href=".config/marksman">marksman</a> — Markdown LSP server</li>
    <li><a href=".config/matplotlib">matplotlib</a> — Python plotting library</li>
    <li><a href=".config/meilisearch">meilisearch</a> — Fast search engine</li>
    <li><a href=".config/mise">mise</a> — Polyglot runtime manager</li>
    <li><a href=".config/monit">monit</a> — System/process monitoring</li>
    <li><a href=".config/mosquitto">mosquitto</a> — MQTT broker</li>
    <li><a href=".config/mpv">mpv</a> — Media player</li>
    <li><a href=".config/msmtp">msmtp</a> — SMTP client</li>
    <li><a href=".config/mumble">mumble</a> — VoIP client</li>
  </ul>
<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```bash
export MSMTP_CONFIG="$XDG_CONFIG_HOME/msmtp/config"
```

</div>
</blockquote>
</details>

<details>
<summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;">
  <strong>N — Neovim, Networking & Nix</strong>
</summary>
<blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
  <ul>
    <li><a href=".config/nano">nano</a> — GNU nano editor</li>
    <li><a href=".config/neomutt">neomutt</a> — Terminal email client</li>
    <li><a href=".config/netctl">netctl</a> — Profile-based network manager</li>
    <li><a href=".config/netdata">netdata</a> — Real-time performance monitoring</li>
    <li><a href=".config/nftables">nftables</a> — Linux firewall ruleset</li>
    <li><a href=".config/niri">niri</a> — Scrollable-tiling Wayland compositor</li>
    <li><a href=".config/nixpkgs">nixpkgs</a> — Nix user package config</li>
    <li><a href=".config/notmuch">notmuch</a> — Fast mail indexer</li>
    <li><a href=".config/npm">npm</a> — Node package manager config</li>
    <li><a href=".config/nvidia">nvidia</a> — NVIDIA driver config</li>
    <li><a href=".config/nwg-displays">nwg-displays</a> — Wayland display manager GUI</li>
  </ul>
<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```bash
npm config set cache "$XDG_CACHE_HOME/npm"
npm config set prefix "$XDG_DATA_HOME/npm"
```

</div>
</blockquote>
</details>

<details>
<summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;">
  <strong>O–P — OpenVPN, Pacman & Pipewire</strong>
</summary>
<blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
  <ul>
    <li><a href=".config/obs-studio">obs-studio</a> — Streaming and recording</li>
    <li><a href=".config/offlineimap">offlineimap</a> — IMAP mail sync</li>
    <li><a href=".config/onionshare">onionshare</a> — Anonymous file sharing</li>
    <li><a href=".config/openrazer">openrazer</a> — Razer peripheral driver</li>
    <li><a href=".config/openvpn">openvpn</a> — VPN daemon config</li>
    <li><a href=".config/pacman">pacman</a> — Arch Linux package manager</li>
    <li><a href=".config/pacman.d">pacman.d</a> — pacman drop-in configs</li>
  </ul>
<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```bash
ls "$XDG_CONFIG_HOME/pacman.d/"
```

</div>
</blockquote>
</details>

<details>
<summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;">
  <strong>P (continued) — Pipewire, Postfix & Proxies</strong>
</summary>
<blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
  <ul>
    <li><a href=".config/pacoloco">pacoloco</a> — Pacman repository proxy</li>
    <li><a href=".config/pacredir">pacredir</a> — Pacman traffic redirector</li>
    <li><a href=".config/pacserve">pacserve</a> — Share pacman packages on LAN</li>
    <li><a href=".config/pamac">pamac</a> — GUI package manager</li>
    <li><a href=".config/pam.d">pam.d</a> — PAM authentication modules</li>
    <li><a href=".config/pam-exec-oauth2">pam-exec-oauth2</a> — OAuth2 PAM module</li>
    <li><a href=".config/pandoc">pandoc</a> — Universal document converter</li>
    <li><a href=".config/pango">pango</a> — Text layout and rendering</li>
    <li><a href=".config/paru">paru</a> — AUR helper config</li>
    <li><a href=".config/pavucontrol-qt">pavucontrol-qt</a> — Qt PulseAudio volume control</li>
    <li><a href=".config/pgbouncer">pgbouncer</a> — PostgreSQL connection pooler</li>
    <li><a href=".config/pgmodeler">pgmodeler</a> — PostgreSQL data modeler</li>
    <li><a href=".config/photoprism">photoprism</a> — AI-powered photo management</li>
    <li><a href=".config/php">php</a> / <a href=".config/php84">php84</a> — PHP interpreter config</li>
    <li><a href=".config/picom">picom</a> — X11 compositor</li>
    <li><a href=".config/pico-tts">pico-tts</a> — SVOX Pico TTS engine</li>
    <li><a href=".config/pip">pip</a> — Python package installer</li>
    <li><a href=".config/piper-tts">piper-tts</a> — Local neural TTS</li>
    <li><a href=".config/pipewire">pipewire</a> — Low-latency audio/video server</li>
    <li><a href=".config/pipewire.conf.d">pipewire.conf.d</a> — PipeWire drop-in configs</li>
    <li><a href=".config/pixi">pixi</a> — Conda-based package manager</li>
    <li><a href=".config/plymouth">plymouth</a> — Boot splash screen</li>
    <li><a href=".config/pnpm">pnpm</a> — Fast Node.js package manager</li>
    <li><a href=".config/polkit-1">polkit-1</a> — Privilege authorization framework</li>
    <li><a href=".config/polybar">polybar</a> — Status bar</li>
    <li><a href=".config/postfix">postfix</a> — SMTP mail transfer agent</li>
    <li><a href=".config/postfix-mysql">postfix-mysql</a> — Postfix MySQL lookups</li>
    <li><a href=".config/postfix-psql">postfix-psql</a> — Postfix PostgreSQL lookups</li>
    <li><a href=".config/postfix-sqlite">postfix-sqlite</a> — Postfix SQLite lookups</li>
    <li><a href=".config/powerdns">powerdns</a> — Authoritative DNS server</li>
    <li><a href=".config/powershell">powershell</a> — PowerShell Core config</li>
    <li><a href=".config/proxychains">proxychains</a> — Proxy chain config</li>
    <li><a href=".config/pulse">pulse</a> — PulseAudio client config</li>
    <li><a href=".config/pytest">pytest</a> — Python testing framework</li>
  </ul>
<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```bash
export PIPEWIRE_CONFIG_DIR="$XDG_CONFIG_HOME/pipewire"
export PIP_CONFIG_FILE="$XDG_CONFIG_HOME/pip/pip.conf"
export PIP_CACHE_DIR="$XDG_CACHE_HOME/pip"
```

</div>
</blockquote>
</details>

<details>
<summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;">
  <strong>Q — QEMU, Qt & Qutebrowser</strong>
</summary>
<blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
  <ul>
    <li><a href=".config/qemu">qemu</a> — QEMU machine emulator config</li>
    <li><a href=".config/qt5ct">qt5ct</a> — Qt5 appearance config</li>
    <li><a href=".config/qt6ct">qt6ct</a> — Qt6 appearance config</li>
    <li><a href=".config/qutebrowser">qutebrowser</a> — Keyboard-driven browser</li>
  </ul>
<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```bash
export QT_QPA_PLATFORMTHEME=qt6ct
export QT_STYLE_OVERRIDE=kvantum
```

</div>
</blockquote>
</details>

<details>
<summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;">
  <strong>R — Redis, Rust & Remote Tools</strong>
</summary>
<blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
  <ul>
    <li><a href=".config/r">r</a> — R language config</li>
    <li><a href=".config/radvd">radvd</a> — IPv6 router advertisement daemon</li>
    <li><a href=".config/redis">redis</a> — In-memory data store</li>
    <li><a href=".config/redsocks2">redsocks2</a> — Transparent SOCKS redirector</li>
    <li><a href=".config/rkhunter">rkhunter</a> — Rootkit hunter config</li>
    <li><a href=".config/ruff">ruff</a> — Fast Python linter/formatter</li>
    <li><a href=".config/rygel">rygel</a> — UPnP/DLNA media server</li>
  </ul>
<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```bash
export RUFF_CONFIG="$XDG_CONFIG_HOME/ruff/ruff.toml"
```

</div>
</blockquote>
</details>

<details>
<summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;">
  <strong>S — Security, SSH, Samba & Syncthing</strong>
</summary>
<blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
  <ul>
    <li><a href=".config/samba">samba</a> — SMB/CIFS file sharing</li>
    <li><a href=".config/sanoid">sanoid</a> — ZFS snapshot manager</li>
    <li><a href=".config/sass">sass</a> — CSS preprocessor</li>
    <li><a href=".config/sccache">sccache</a> — Compiler cache (Rust/C/C++)</li>
    <li><a href=".config/searchsploit">searchsploit</a> — ExploitDB CLI</li>
    <li><a href=".config/selene">selene</a> — Lua linter</li>
    <li><a href=".config/shadowsocks-rust">shadowsocks-rust</a> — Encrypted proxy protocol</li>
    <li><a href=".config/shellcheck">shellcheck</a> — Shell script static analysis</li>
    <li><a href=".config/signal">signal</a> — Signal desktop messenger</li>
    <li><a href=".config/smartdns">smartdns</a> — High-performance DNS server</li>
    <li><a href=".config/softhsm2">softhsm2</a> — Software HSM implementation</li>
    <li><a href=".config/soju">soju</a> — IRC bouncer</li>
    <li><a href=".config/speech-dispatcher">speech-dispatcher</a> — Speech synthesis interface</li>
    <li><a href=".config/ssh">ssh</a> — OpenSSH client config</li>
    <li><a href=".config/sshguard">sshguard</a> — SSH brute-force protection</li>
    <li><a href=".config/sshuttle">sshuttle</a> — VPN-over-SSH tunnel</li>
    <li><a href=".config/sssd">sssd</a> — System security services daemon</li>
    <li><a href=".config/stalwart-mail">stalwart-mail</a> — Modern mail server</li>
    <li><a href=".config/steam">steam</a> — Steam gaming client</li>
    <li><a href=".config/strongswan">strongswan</a> — IPsec VPN</li>
    <li><a href=".config/stunnel">stunnel</a> — SSL/TLS tunneling</li>
    <li><a href=".config/subversion">subversion</a> — SVN version control</li>
    <li><a href=".config/supermaven">supermaven</a> — AI code completion</li>
    <li><a href=".config/sway">sway</a> — Wayland i3-compatible compositor</li>
    <li><a href=".config/syncthing">syncthing</a> — Continuous file synchronization</li>
    <li><a href=".config/systemd">systemd</a> — systemd user units and config</li>
  </ul>
<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```bash
export SSH_CONFIG="$XDG_CONFIG_HOME/ssh/config"
alias ssh='ssh -F "$XDG_CONFIG_HOME/ssh/config"'

export SCCACHE_DIR="$XDG_CACHE_HOME/sccache"
```

</div>
</blockquote>
</details>

<details>
<summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;">
  <strong>T — Tailscale, Tmux, Tor & Traefik</strong>
</summary>
<blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
  <ul>
    <li><a href=".config/tailscale">tailscale</a> — WireGuard-based mesh VPN</li>
    <li><a href=".config/tailwind">tailwind</a> — Tailwind CSS config</li>
    <li><a href=".config/taplo">taplo</a> — TOML LSP and formatter</li>
    <li><a href=".config/tarantool">tarantool</a> — In-memory database</li>
    <li><a href=".config/tenacity">tenacity</a> — Audacity fork audio editor</li>
    <li><a href=".config/texlive">texlive</a> — LaTeX distribution config</li>
    <li><a href=".config/timeshift">timeshift</a> — System restore utility</li>
    <li><a href=".config/thunar">thunar</a> — XFCE file manager</li>
    <li><a href=".config/tlp">tlp</a> — Linux power management</li>
    <li><a href=".config/tmux">tmux</a> — Terminal multiplexer</li>
    <li><a href=".config/tombi">tombi</a> — TOML language toolchain</li>
    <li><a href=".config/tor">tor</a> — Tor anonymity network</li>
    <li><a href=".config/torbrowser">torbrowser</a> — Tor Browser config</li>
    <li><a href=".config/traefik">traefik</a> — Cloud-native reverse proxy</li>
    <li><a href=".config/tree-sitter">tree-sitter</a> — Incremental parsing library</li>
  </ul>
<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```bash
export TMUX_CONFIG="$XDG_CONFIG_HOME/tmux/tmux.conf"
# source-file $XDG_CONFIG_HOME/tmux/tmux.conf
```

</div>
</blockquote>
</details>

<details>
<summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;">
  <strong>U — udev, UFW, Unbound & usbguard</strong>
</summary>
<blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
  <ul>
    <li><a href=".config/udev">udev</a> — Device event management rules</li>
    <li><a href=".config/udisks2">udisks2</a> — Disk management daemon</li>
    <li><a href=".config/ufw">ufw</a> — Uncomplicated firewall</li>
    <li><a href=".config/unbound">unbound</a> — Validating DNS resolver</li>
    <li><a href=".config/unbound/unbound.conf">unbound/unbound.conf</a> — Main resolver config</li>
    <li><a href=".config/unbound/rpz">unbound/rpz</a> — Response Policy Zones</li>
    <li><a href=".config/upower">upower</a> — Power device daemon</li>
    <li><a href=".config/uptime-kuma">uptime-kuma</a> — Self-hosted uptime monitor</li>
    <li><a href=".config/usbguard">usbguard</a> — USB device authorization</li>
    <li><a href=".config/uwsgi">uwsgi</a> — WSGI application server</li>
    <li><a href=".config/uwsm">uwsm</a> — Universal Wayland session manager</li>
  </ul>
<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```bash
bash "$XDG_CONFIG_HOME/unbound/clearnet.sh"
bash "$XDG_CONFIG_HOME/unbound/rotate.sh"
```

</div>
</blockquote>
</details>


<details>
<summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;">
  <strong>V — Vault, Virt, VLC & VPN</strong>
</summary>
<blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
  <ul>
    <li><a href=".config/v2ray">v2ray</a> — Universal proxy platform</li>
    <li><a href=".config/vagrant">vagrant</a> — VM environment manager</li>
    <li><a href=".config/vale">vale</a> — Prose linter</li>
    <li><a href=".config/valkey">valkey</a> — Redis-compatible key-value store</li>
    <li><a href=".config/vault">vault</a> — HashiCorp secrets manager</li>
    <li><a href=".config/vaultwarden">vaultwarden</a> — Self-hosted Bitwarden server</li>
    <li><a href=".config/vcpkg">vcpkg</a> — C/C++ package manager</li>
    <li><a href=".config/vectorcode">vectorcode</a> — Codebase vector search tool</li>
    <li><a href=".config/vencord">vencord</a> — Discord client mod</li>
    <li><a href=".config/vfio-kvm">vfio-kvm</a> — GPU passthrough config</li>
    <li><a href=".config/vkBasalt">vkBasalt</a> — Vulkan post-processing layer</li>
    <li><a href=".config/vlc">vlc</a> — VLC media player</li>
    <li><a href=".config/vpnc">vpnc</a> — Cisco VPN client</li>
    <li><a href=".config/vsftpd">vsftpd</a> — Very secure FTP daemon</li>
  </ul>
<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```bash
export VAULT_CONFIG_PATH="$XDG_CONFIG_HOME/vault/vault.hcl"
```

</div>
</blockquote>
</details>

<details>
<summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;">
  <strong>W — Waybar, Wireplumber & Wayland</strong>
</summary>
<blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
  <ul>
    <li><a href=".config/wallust">wallust</a> — Color scheme generator from wallpapers</li>
    <li><a href=".config/waybar">waybar</a> — Wayland bar for Sway/Hyprland</li>
    <li><a href=".config/waypaper">waypaper</a> — Wallpaper manager GUI</li>
    <li><a href=".config/webhook">webhook</a> — Lightweight webhook server</li>
    <li><a href=".config/wget">wget</a> — GNU wget config</li>
    <li><a href=".config/wifite">wifite</a> — Automated wireless auditor</li>
    <li><a href=".config/wiremix">wiremix</a> — PipeWire TUI mixer</li>
    <li><a href=".config/wireplumber">wireplumber</a> — PipeWire session manager</li>
    <li><a href=".config/wireshark">wireshark</a> — Network protocol analyzer</li>
    <li><a href=".config/wlogout">wlogout</a> — Wayland logout menu</li>
    <li><a href=".config/wofi">wofi</a> — Wayland application launcher</li>
  </ul>
<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```bash
export WGETRC="$XDG_CONFIG_HOME/wget/wgetrc"
```

</div>
</blockquote>
</details>


<details>
<summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;">
  <strong>X — XDG, X11 & XFCE</strong>
</summary>
<blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
  <ul>
    <li><a href=".config/x11">x11</a> — X Window System config</li>
    <li><a href=".config/xdg">xdg</a> — XDG user dirs and MIME config</li>
    <li><a href=".config/xdg-desktop-portal">xdg-desktop-portal</a> — Flatpak portal config</li>
    <li><a href=".config/xdg-ninja">xdg-ninja</a> — XDG compliance checker config</li>
    <li><a href=".config/xdg-terminal-exec">xdg-terminal-exec</a> — Default terminal config</li>
    <li><a href=".config/xfce4">xfce4</a> — XFCE desktop environment</li>
    <li><a href=".config/xkbsel">xkbsel</a> — XKB keyboard layout selector</li>
    <li><a href=".config/xmake">xmake</a> — Lua-based build system</li>
  </ul>
<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```bash
"$XDG_CONFIG_HOME/user-dirs.dirs"
"$XDG_CONFIG_HOME/user-dirs.locale"
```

</div>
</blockquote>
</details>

<details>
<summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;">
  <strong>Y — YAML, Yay & YARA</strong>
</summary>
<blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
  <ul>
    <li><a href=".config/yamlls">yamlls</a> — YAML language server</li>
    <li><a href=".config/yara">yara</a> — Malware classification rules</li>
    <li><a href=".config/yay">yay</a> — AUR helper (Yet Another Yogurt)</li>
  </ul>
<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```bash
export YAY_CONFIG="$XDG_CONFIG_HOME/yay/config.json"
```

</div>
</blockquote>
</details>


<details>
<summary style="font-size: 1.4em; font-weight: bold; padding: 15px; background: #667eea; color: white; border-radius: 10px; cursor: pointer; margin: 10px 0; display: flex; align-items: center; gap: 8px;">
  <strong>Z — Zed, Zig, ZLS & Zotero</strong>
</summary>
<blockquote style="font-size: 1.2em; line-height: 1.8; padding: 25px; background: #f8f9fa; border-left: 6px solid #667eea; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
  <ul>
    <li><a href=".config/zabbix">zabbix</a> — Enterprise monitoring platform</li>
    <li><a href=".config/zed">zed</a> — High-performance code editor</li>
    <li><a href=".config/zfsbootmenu">zfsbootmenu</a> — ZFS boot environment manager</li>
    <li><a href=".config/zig">zig</a> — Zig language toolchain config</li>
    <li><a href=".config/zigbee2mqtt">zigbee2mqtt</a> — Zigbee to MQTT bridge</li>
    <li><a href=".config/zls">zls</a> — Zig language server</li>
    <li><a href=".config/zotero-translation-server">zotero-translation-server</a> — Zotero web translator</li>
  </ul>
<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 10px; font-family: monospace;">

```bash
export ZLS_CONFIG_PATH="$XDG_CONFIG_HOME/zls/zls.json"
export ZIG_GLOBAL_CACHE_DIR="$XDG_CACHE_HOME/zig"
```

</div>
</blockquote>
</details>

</div>

---

## XDG Base Directory Compliance

All configs follow the [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/latest/):

| Variable | Default | Purpose |
|---|---|---|
| `$XDG_CONFIG_HOME` | `~/.config` | User config files |
| `$XDG_DATA_HOME` | `~/.local/share` | User data files |
| `$XDG_CACHE_HOME` | `~/.cache` | Non-essential cached data |
| `$XDG_STATE_HOME` | `~/.local/state` | Persistent state data |
| `$XDG_RUNTIME_DIR` | `/run/user/$UID` | Runtime/socket files |

---

## License

Copyright (C) 2026 Qompass AI, All rights reserved — [GQL License](https://github.com/qompassai/GQL)
