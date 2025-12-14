#!/usr/bin/env bash
# /qompassai/dotfiles/.config/bash.d/git.bash
# Qompass AI Bash.d Git Bash Config
alias gitlog="git log --graph --decorate"
alias gitlogg="git log --graph --decorate --full-history"

gitcom() {
    git commit --signoff -m "$*"
}

gitcomm() {
    git commit --signoff -S"$GPG_KEY" -m "$*"
}

ge() {
    if [ -z "$EDITOR" ]; then
        printf '\e[1;31m%s\e[0m\n' 'No default editor is set, please configure the environment variable EDITOR'
    else
        $EDITOR -- "$@"
        git add -- "$@"
    fi
}

gitpush() {
    git push -u origin $(___git_branch_)
}

gitpull() {
    __gb_=$(___git_branch_)
    git checkout "$1" &&
        git pull &&
        git checkout $__gb_ &&
        git pull . "$1"
}

gitp() {
    __gb_=$(___git_branch_)
    git pull &&
        git checkout "$1" &&
        git pull &&
        git pull . $__gb_
}

_____gp___bashrc_() {
    printf '%s\n' "$2"
}
_____gp__bashrc_() {
    _____gp___bashrc_ $(git status -b -s 2>/dev/null)
}
___git_branch_() {
    printf '%s\n' $(_____gp__bashrc_ | cut -d . -f 1)
}
