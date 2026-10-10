# Architectural Decisions — dotfiles

## XDG layout (standing)

**Decision**: XDG base-directory layout on primo. `~/.config/nvim`
symlinks to `~/workspace/repos/diver`.

## Skill locations (2026-09-30)

**Decision**: Nvim-specific skills at `$XDG_DATA_HOME/nvim/skills/`,
general skills at `$XDG_DATA_HOME/skills/`. Byte-identical mirrors
into Diver `skills/`.

**Consequence**: Single source of truth per skill; push script preserves
modes and paths.
