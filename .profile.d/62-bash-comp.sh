# ~/.profile.d/62-bash-comp.sh
[[ $- == *i* ]] || return
type complete &>/dev/null || return
if [ -f "$HOME/.local/share/bash-completion/completions/complete_alias" ]; then
    . "$HOME/.local/share/bash-completion/completions/complete_alias"
    complete -F _complete_alias "${!BASH_ALIASES[@]}"
fi
