# /qompassai/dotfiles/.config/fish/conf.d/mail.fish
# Qompass AI Fish Mail Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
function dovecot
    command dovecot -c $XDG_CONFIG_HOME/dovecot/dovecot.conf $argv
end
