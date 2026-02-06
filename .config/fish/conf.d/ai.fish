# ai.fish
# Qompass AI - [ ]
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
set -gx AI_SKILLS_DIR "$XDG_CONFIG_HOME/skills"
if not test -d "$AI_SKILLS_DIR"
    mkdir -p "$AI_SKILLS_DIR"
end
