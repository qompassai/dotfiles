# SSH/GPG Agent
set -x SSH_AUTH_SOCK (gpgconf --list-dirs agent-ssh-socket)
set -e SSH_AGENT_PID
eval (ssh-agent -c)
