# Current Work — dotfiles

Matt's dotfiles (qompassai/dotfiles). XDG base-directory layout.

## Active (2026-10-04)

- Primo uses XDG layout; `~/.config/nvim` symlinks to diver repo.
- Skills live at `$XDG_DATA_HOME/nvim/skills/` (nvim-specific) and
  `$XDG_DATA_HOME/skills/` (general), byte-identical into Diver `skills/`.
- Skill push tool: `~/workspace/diver-push/push_primo_tree.py`
  (primo→GitHub API, preserves modes).

## Standing rules

- Commit/push once WIP is resolved (per Matt's direction).
- Salesforce skills (salesforce-trailblazer, apex-dev) shipped here.
- Trailhead has NO public completion API (org-side only).
