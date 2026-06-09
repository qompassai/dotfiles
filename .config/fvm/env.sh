[ -f "${XDG_CONFIG_HOME:-$HOME/.config}/fvm/config.env" ] && \
  . "${XDG_CONFIG_HOME:-$HOME/.config}/fvm/config.env"
alias flutter='fvm flutter'
alias dart='fvm dart'
