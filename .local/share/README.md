<!-- /qompassai/Dotfiles/.local/share/README.md -->
<!-- Qompass AI Dotfiles Data Docs -->
<!-- Copyright (C) 2026 Qompass AI, All rights reserved -->
<!-- ---------------------------------------- -->

<div align="center">

<img src="https://raw.githubusercontent.com/qompassai/svg/refs/heads/main/assets/qompass/qompass.svg" alt="Qompass AI" width="120" height="120" />

# Qompass AI Dotfiles

**XDG-compliant data files for the Qompass AI development environment**

![Arch Linux](https://img.shields.io/badge/Arch_Linux-1793D1?style=for-the-badge&logo=arch-linux&logoColor=white)
![Hyprland](https://img.shields.io/badge/Hyprland-58E1FF?style=for-the-badge&logo=hyprland&logoColor=black)
![License](https://img.shields.io/badge/License-GQL-667eea?style=for-the-badge)

</div>

---

## Overview

All data files follow X Desktop Group (XDG) convention `$XDG_DATA_HOME` (`~/.local/share`).
This directory maps 1:1 onto the live home directory: `.local/share/X` here is `~/.local/share/X` on the machine.

---

## Apps (A–Z)

Every entry in this directory, alphabetical by app name. Click an entry to open its directory.

| App | Description |
| --- | --- |
| [applications](./applications) | Desktop entries (.desktop files) |
| [skills](./skills) | Agent Skills installed at `$XDG_DATA_HOME/skills` |

---

## Skills (A–Z)

General (non-Neovim-specific) Agent Skills. Neovim-specific skills live in the
Diver config (`.config/nvim` submodule) and at `$XDG_DATA_HOME/nvim/skills`.

| Skill | Description |
| --- | --- |
| [arch-provision](./skills/arch-provision) | Fresh-machine Arch provisioning: install order, packages.yml, snapper, NVIDIA |
| [arch-system-update](./skills/arch-system-update) | Full ordered Arch update ritual: snapper snapshots, pacman/paru/flatpak, orphan cleanup |
| [aur-malware-scan](./skills/aur-malware-scan) | Incident-response scan for the June 2026 atomic-lockfile AUR supply-chain attack |
| [frontend-design](./skills/frontend-design) | Distinctive visual design for HTML report briefs, review packs, and rose.nvim UI surfaces |
| [hyprland-session](./skills/hyprland-session) | Hyprland session ops: wake monitors after sleep, reload with quickshell bar, layout toggle |
| [internal-comms](./skills/internal-comms) | Internal communications for Qompass AI in Matt's plain, evidence-based voice (3P updates) |
| [mcp-builder](./skills/mcp-builder) | Build and harden MCP servers and clients for the Neovim-first stack |
| [rosenpass-pqc-vpn](./skills/rosenpass-pqc-vpn) | Post-quantum-secure WireGuard tunnels via Rosenpass key exchange |
| [skill-creator](./skills/skill-creator) | Guides creation, modification, and improvement of Agent Skills for Neovim-centered workflows |

---

## Neovim Skills (A–Z)

Neovim-specific Agent Skills, installed at `$XDG_DATA_HOME/nvim/skills`. These require Matt's
Diver Neovim config (its Lua modules, `lsp/` configs, DAP adapters, and `:Sf*` commands) —
see the root README's Agent Skills section for the full write-up.

| Skill | Description |
| --- | --- |
| [apex-dev](./nvim/skills/apex-dev) | Full Salesforce Apex loop in Neovim: Apex LSP edit, apexfmt, Code Analyzer lint, `sf` test runs, deploy/retrieve, interactive + replay DAP debug, SOQL |
| [salesforce-trailblazer](./nvim/skills/salesforce-trailblazer) | Work Salesforce Trailhead modules asynchronously via Diver's Trailhead job queue and the `sf` CLI |
