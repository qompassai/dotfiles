# Patterns — dotfiles

## Skill sync

- `~/workspace/diver-push/push_primo_tree.py`: primo→GitHub API,
  preserves file modes. Use for skill tree pushes.
- Skills mined from: dotfiles (arch-provision, arch-system-update,
  aur-malware-scan, hyprland-session, rosenpass-pqc-vpn), Salesforce,
  Anthropic adaptations (with upstream LICENSE.txt verbatim).

## Repomap (codebase map for agents)

One-shot generation (no flake wiring in this repo):

```
nix run github:qompassai/nix?dir=repomap -- /path/to/repo --budget 15000 --out .repomap.txt
```

`.repomap.txt` is a derived artifact — gitignore it, never commit it.
For automatic regeneration on `nix develop`, wire the flake input per
github.com/qompassai/nix/tree/main/repomap/README.md.
