# /qompassai/Dotfiles/scripts/exports.sh
# -----------------------------------------
# Copyright (C) 2025 Qompass AI, All rights reserved

# shellcheck shell=bash
function add_to_path() {
  if [ -d "$2" ]; then
    if [[ ":$PATH:" == *":$2:"* ]]; then
      remove_from_path "$2"
    fi

    if [ "$1" = "prepend" ]; then
      PATH="$2:$PATH"
      export PATH
    elif [ "$1" = "append" ]; then
      PATH="$PATH:$2"
      export PATH
    else
      echo "Unknown option. Use 'prepend' or 'append'."
    fi
  fi
  local path_to_remove="$1"
  if [[ -n "$path_to_remove" && ":$PATH:" == *":$path_to_remove:"* ]]; then
    while [[ ":$PATH:" == *":$path_to_remove:"* ]]; do
      # Remove
      PATH="${PATH/#$path_to_remove:/}"
      PATH="${PATH/%:$path_to_remove/}"
      PATH="${PATH//:$path_to_remove:/:}"
    done
    PATH="${PATH#:}"
    PATH="${PATH%:}"
    export PATH
  fi
}
if [ -n "${ZSH_VERSION}" ]; then
  shell="zsh"
  export DOTFILES_DEBUG_SHELL_ZSH="true"
elif [ -n "${BASH_VERSION}" ]; then
  shell="bash"
  export DOTFILES_DEBUG_SHELL_BASH="true"
else
  shell=""
fi

if [ -f /opt/homebrew/bin/brew ]; then
  eval "$(/opt/homebrew/bin/brew shellenv)"
  brew_prefix="$(brew --prefix)"
elif [ -f /home/linuxbrew/.linuxbrew/bin/brew ]; then
  eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
  brew_prefix="$(brew --prefix)"
else
  echo "Please install Homebrew and the Brewfile."
  brew_prefix=""
fi

export DOTFILES="$HOME/.dotfiles"
export DOTFILES_SHELL=$shell
export DOTFILES_BREW_PREFIX=$brew_prefix
export HOMEBREW_NO_ANALYTICS=1
export PIP_REQUIRE_VIRTUALENV=true
export PYENV_ROOT="$HOME/.pyenv"
export GIT_EDITOR="nvim"
export EDITOR="nvim"
add_to_path append "$HOME/.docker/bin"
add_to_path append "$HOME/.cargo/bin"
add_to_path append "$HOME/go/bin"
add_to_path append "$DOTFILES_BREW_PREFIX/opt/mysql-client/bin"
add_to_path prepend "$DOTFILES_BREW_PREFIX/opt/gnu-sed/libexec/gnubin"
add_to_path prepend "$PYENV_ROOT/bin"
add_to_path prepend "$HOME/.local/bin"
add_to_path prepend "$DOTFILES/shell/bin"
# shellcheck disable=SC1090
if [ -f "$HOME/.shell/.env" ]; then
  set -a
  source $HOME/.shell/.env
  set +a
else
  echo "Warning: $HOME/.shell/.env does not exist"
fi

case $(uname) in
Darwin)
  add_to_path append "/Applications/Visual Studio Code.app/Contents/Resources/app/bin"
  if command -v colima &>/dev/null; then
    export DOCKER_HOST="unix://$HOME/.colima/docker.sock"
  fi

  # # nvm
  # if [ "$(uname -m)" = "arm64" ]; then
  # 	export NVM_DIR="$HOME/.nvm"
  # elif [ "$(uname -m)" = "x86_64" ]; then
  # 	export NVM_DIR="$HOME/.nvm_x86"
  # fi

  ;;

Linux)
  # commands for Linux go here

  # export NVM_DIR="$HOME/.nvm"

  ;;

*) ;;
esac
