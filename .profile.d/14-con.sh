export DOCKER_BUILDKIT=1
export DOCKER_CONFIG="$XDG_CONFIG_HOME/docker"
export DOCKER_HOST=unix:///run/user/$(id -u)/docker.sock
