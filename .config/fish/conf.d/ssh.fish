# /qompassai/dotfiles/fish/conf.d/ssh.fish
# Qompass AI Fish Secure Shell (SSH) Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
if test -n "$XDG_RUNTIME_DIR"
    set -gx SSH_AUTH_SOCK "$XDG_RUNTIME_DIR/ssh-agent.socket"
else
    set -gx SSH_AUTH_SOCK "$XDG_RUNTIME_DIR/ssh-agent.socket"
end
set -xU SSH_AUTH_SOCK $XDG_RUNTIME_DIR/ssh-agent.socket #
set -e SSH_AGENT_PID #
#eval (ssh-agent -c)
