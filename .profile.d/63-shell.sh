#!/usr/bin/env sh
# /qompassai/Shell/.profile.d/62-shell.sh
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################

[[ $- == *i* ]] || return

export EDITOR="${EDITOR:-nvim}"
export HISTCONTROL="ignoreboth:erasedups"
export HISTFILESIZE=100000
export HISTSIZE=50000
export HISTTIMEFORMAT="%Y-%m-%d %H:%M:%S "
export PAGER="${PAGER:-less}"

CURRENT_SHELL=$(basename "$SHELL")
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias c='clear'
alias df='df -h'
alias du='du -h'
alias g='git'
alias grep='grep --color=auto'
alias h='history'
alias l='ls -CF'
alias la='ls -A'
alias ll='ls -alF'
alias ls='ls --color=auto'
alias mkdir='mkdir -pv'
alias mv='mv -i'
alias ports='netstat -tulanp'
alias ps='ps aux'
alias rm='rm -i'
alias top='htop'
alias vi='vim'

if [ "$CURRENT_SHELL" = "bash" ]; then
    type complete &>/dev/null || return

    if [ -f /usr/share/bash-completion/bash_completion ]; then
        . /usr/share/bash-completion/bash_completion
    elif [ -f /etc/bash_completion ]; then
        . /etc/bash_completion
    fi

    if [ -f "$HOME/.local/share/bash-completion/completions/complete_alias" ]; then
        . "$HOME/.local/share/bash-completion/completions/complete_alias"
        complete -F _complete_alias "${!BASH_ALIASES[@]}"
    fi

    if [ -d "$HOME/.local/share/bash-completion/completions" ]; then
        for completion in "$HOME/.local/share/bash-completion/completions"/*; do
            [ -r "$completion" ] && . "$completion"
        done
    fi

    shopt -s autocd 2>/dev/null
    shopt -s cdspell 2>/dev/null
    shopt -s checkwinsize 2>/dev/null
    shopt -s dirspell 2>/dev/null
    shopt -s globstar 2>/dev/null
    shopt -s histappend 2>/dev/null
    shopt -s nocaseglob 2>/dev/null
fi

if [ "$CURRENT_SHELL" = "fish" ]; then
    export fish_greeting=""
    export fish_user_paths="$HOME/.local/bin:$fish_user_paths"
fi

if [ "$CURRENT_SHELL" = "nu" ] || [ "$CURRENT_SHELL" = "nushell" ]; then
    export NU_LIB_DIRS="$HOME/.config/nushell/lib"
    export NU_PLUGIN_DIRS="$HOME/.config/nushell/plugins"
fi

if [ "$CURRENT_SHELL" = "zsh" ]; then
    autoload -U compinit && compinit
    setopt AUTO_CD
    setopt AUTO_PUSHD
    setopt COMPLETE_IN_WORD
    setopt EXTENDED_GLOB
    setopt HIST_EXPIRE_DUPS_FIRST
    setopt HIST_FIND_NO_DUPS
    setopt HIST_IGNORE_ALL_DUPS
    setopt HIST_IGNORE_DUPS
    setopt HIST_IGNORE_SPACE
    setopt HIST_REDUCE_BLANKS
    setopt HIST_SAVE_NO_DUPS
    setopt HIST_VERIFY
    setopt INC_APPEND_HISTORY
    setopt INTERACTIVE_COMMENTS
    setopt NO_BEEP
    setopt PUSHD_IGNORE_DUPS
    setopt SHARE_HISTORY
    zstyle ':completion:*' auto-description 'specify: %d'
    zstyle ':completion:*' completer _expand _complete _correct _approximate
    zstyle ':completion:*' format 'Completing %d'
    zstyle ':completion:*' group-name ''
    zstyle ':completion:*' list-colors ${(s.:.)LS_COLORS}
    zstyle ':completion:*' list-colors ''
    zstyle ':completion:*' list-prompt %SAt %p: Hit TAB for more, or the character to insert%s
    zstyle ':completion:*' matcher-list '' 'm:{a-z}={A-Z}' 'm:{a-zA-Z}={A-Za-z}' 'r:|[._-]=* r:|=* l:|=*'
    zstyle ':completion:*' menu select=2
    zstyle ':completion:*' menu select=long
    zstyle ':completion:*' select-prompt %SScrolling active: current selection at %p%s
    zstyle ':completion:*' use-compctl false
    zstyle ':completion:*' verbose true
    zstyle ':completion:*:*:kill:*:processes' list-colors '=(#b) #([0-9]#)*=0=01;31'
    zstyle ':completion:*:kill:*' command 'ps -u $USER -o pid,%cpu,tty,cputime,cmd'
fi


reload_shell() {
    case "$CURRENT_SHELL" in
        bash)
            source "$HOME/.bashrc"
            ;;
        zsh)
            source "$HOME/.zshrc"
            ;;
        fish)
            exec fish
            ;;
        nu|nushell)
            exec nu
            ;;
        *)
            echo "Unknown shell: $CURRENT_SHELL"
            ;;
    esac
}

setup_shell_configs() {
    echo "Setting up shell configuration files..."

    if command -v fish >/dev/null; then
        mkdir -p "$HOME/.config/fish"
        [ ! -f "$HOME/.config/fish/config.fish" ] && echo "# Fish configuration" > "$HOME/.config/fish/config.fish"
    fi

    if command -v nu >/dev/null; then
        mkdir -p "$HOME/.config/nushell"
        [ ! -f "$HOME/.config/nushell/config.nu" ] && echo "# Nushell configuration" > "$HOME/.config/nushell/config.nu"
        [ ! -f "$HOME/.config/nushell/env.nu" ] && echo "# Nushell environment" > "$HOME/.config/nushell/env.nu"
    fi

    echo "Shell configurations created."
}

shell_benchmark() {
    local shell_cmd="$1"
    [ -z "$shell_cmd" ] && shell_cmd="$SHELL"

    echo "Benchmarking $shell_cmd startup time..."
    for i in {1..5}; do
        time "$shell_cmd" -i -c exit 2>&1 | grep real
    done
}

shell_info() {
    echo "=== Shell Information ==="
    echo "Current shell: $CURRENT_SHELL"
    echo "Shell version: $($SHELL --version | head -1)"
    echo "Shell path: $SHELL"
    echo "Interactive: $([[ $- == *i* ]] && echo "Yes" || echo "No")"
    echo ""

    case "$CURRENT_SHELL" in
        bash)
            echo "Bash options: $(set -o | grep on | cut -d' ' -f1 | tr '\n' ' ')"
            ;;
        zsh)
            echo "Zsh options: $(setopt 2>/dev/null | head -5 | tr '\n' ' ')..."
            ;;
    esac
}

export -f reload_shell setup_shell_configs shell_benchmark shell_info 2>/dev/null || true

