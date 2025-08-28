# dovecot.fish
# Qompass AI Dovcot Fish
# Copyright (C) 2025 Qompass AI, All rights reserved
# ----------------------------------------
function dovecot
    command dovecot -c $HOME/.config/dovecot/dovecot.conf $argv
end

