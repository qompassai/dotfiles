if [ -z "${SSH_AUTH_SOCK-}" ] || ! [ -S "$SSH_AUTH_SOCK" ]; then
  eval "$(ssh-agent -s)"
fi

export GPG_TTY=$(tty)

if [ -f "$HOME/.ssh/authorized_keys.enc" ]; then
  sops -d "$HOME/.ssh/authorized_keys.enc" | ssh-add -L
fi
