export MOJO_HOME="$HOME/.modular"
export MOJO_BIN="$MOJO_HOME/bin"
export PATH="$MOJO_BIN:$PATH"
export MOJO_PROJECT_ROOT="$HOME/dev/my_mojo_project"
export MOJO_TOML="$MOJO_PROJECT_ROOT/mojo.toml"
export MOJO_PROJECT_TOML="$MOJO_PROJECT_ROOT/mojoproject.toml"
export PIXI_TOML="$MOJO_PROJECT_ROOT/pixi.toml"
export MOJO_CACHE_DIR="$XDG_CACHE_HOME/mojo"
export MOJO_RATTLER_CACHE_DIR="$XDG_CACHE_HOME/mojo/rattler"
export MOJO_BUILD_THREADS="$(nproc)"
export MODO_THEME="default"
export MODO_OUTPUT_DIR="$MOJO_PROJECT_ROOT/docs"
export RATTLER_BUILD_BIN="/usr/bin/rattler-build"
if [ -d "$HOME/.pixi/bin" ]; then
  export PATH="$HOME/.pixi/bin:$PATH"
fi
if [ -d "$HOME/.modular/pkg/magic/bin" ]; then
  export PATH="$HOME/.modular/pkg/magic/bin:$PATH"
fi
#if [ -x "/opt/miniconda3/bin/conda" ]; then
#  export CONDA_HOME="/opt/miniconda3"
#  export PATH="$CONDA_HOME/bin:$PATH"
#elif [ -x "/opt/miniforge/bin/conda" ]; then
#  export CONDA_HOME="/opt/miniforge"
#  export PATH="$CONDA_HOME/bin:$PATH"
#fi
export PATH="$PATH:/home/$USER/.modular/bin"
eval "$(magic completion --shell bash)"
# source "$CONDA_HOME/etc/profile.d/conda.sh"
export LD_LIBRARY_PATH=/$HOME/$USER/.local/lib/arch-mojo:$LD_LIBRARY_PATH
#[ -f /opt/miniforge/etc/profile.d/conda.sh ] && source /opt/miniforge/etc/profile.d/conda.sh
