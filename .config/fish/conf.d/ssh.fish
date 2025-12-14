# /qompassai/dotfiles/fish/conf.d/ssh.fish
# Qompass AI Fish Secure Shell (SSH) Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
set -gx SSH_AUTH_SOCK "$XDG_RUNTIME_DIR/ssh-agent.socket"
set -e SSH_AGENT_PID
if not pgrep -u (id -u) ssh-agent >/dev/null 2>&1
    eval (ssh-agent -c | sed -n '1,3p')
end
set -gx SSH_ASKPASS_REQUIRE prefer
set -gx SSH_ASKPASS /usr/bin/pass-sshaskpass
set list "$XDG_CONFIG_HOME/ssh/.list"
if test -f $list
    for ident in (cat $list)
        if test -f $ident
            ssh-add $ident </dev/null
        end
    end
end
