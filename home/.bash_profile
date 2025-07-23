#/qompassai/Shell/bash/.bash_profile
# Qompass AI Bash Profile
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################

if [ -d "$HOME/.profile.d" ]; then
  for profile_script in "$HOME/.profile.d/"*.sh; do
    [ -r "$profile_script" ] && [ -f "$profile_script" ] && source "$profile_script"
  done
fi
eval "$(zoxide init bash)"
