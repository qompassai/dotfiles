# /qompassai/dotfiles/fish/conf.d/ssh.fish
# Qompass AI Fish Secure Shell (SSH) Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
if not test -d "$XDG_RUNTIME_DIR/ssh/control"
    mkdir -p "$XDG_RUNTIME_DIR/ssh/control"
    chmod 700 "$XDG_RUNTIME_DIR/ssh" "$XDG_RUNTIME_DIR/ssh/control"
end
if not set -q SSH_AUTH_SOCK
    set -gx SSH_AUTH_SOCK "$XDG_RUNTIME_DIR/ssh-agent.socket"
end
set -e SSH_AGENT_PID
if not test -S "$SSH_AUTH_SOCK"
    eval (ssh-agent -c | sed -n '1,3p')
end
if set -q WAYLAND_DISPLAY; or set -q DISPLAY
    set -gx SSH_ASKPASS /usr/bin/pass-sshaskpass
    set -gx SSH_ASKPASS_REQUIRE prefer
end
set list "$XDG_CONFIG_HOME/ssh/.list"
if test -f "$list"
    for ident in (cat "$list")
        set expanded (string replace -r '^\$HOME' $HOME $ident)
        if test -f "$expanded"
            ssh-add "$expanded" </dev/null
        end
    end
end
