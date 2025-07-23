# Python/Pyenv
if command -q pyenv
    pyenv init - | source
end
set -x VIRTUAL_ENV $HOME/.venv/nvim
set -x PATH $VIRTUAL_ENV/bin $PATH

