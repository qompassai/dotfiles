#!/bin/bash
VENV_PATH="$HOME/.venv/nvim"
if [ ! -d "$VENV_PATH" ]; then
  python3 -m venv "$VENV_PATH"
  "$VENV_PATH/bin/pip" install --upgrade pip pynvim
fi
echo "Neovim Python venv ready at $VENV_PATH"
