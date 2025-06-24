#!/bin/bash
# Universal profile loader
if [ -n "$FISH_VERSION" ]; then
  return 0
elif [ -n "$NU_VERSION" ]; then
  return 0
elif [ -n "$ZSH_VERSION" ]; then
  CURRENT_SHELL="zsh"
elif [ -n "$BASH_VERSION" ]; then
  CURRENT_SHELL="bash"
else
  CURRENT_SHELL="unknown"
fi

if [[ -z $DISPLAY && $(tty) == "/dev/tty1" ]]; then
  if uwsm check may-start; then
    exec uwsm start hyprland.desktop
  fi
fi
