#!/usr/bin/env bash
# /qompassai/Shell/.profile.d/56-python.sh
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################

export BLACK_CACHE_DIR="$HOME/.cache/black"
#export CONDA_AUTO_ACTIVATE_BASE=false
export HF_HOME="$HOME/.cache/huggingface"
export IPYTHON_DIR="$HOME/.config/ipython"
export JUPYTER_CONFIG_DIR="$HOME/.config/jupyter"
export MPLCONFIGDIR="$HOME/.config/matplotlib"
export NINJA_MAX_PER_PAGE_SIZE=200
export NINJA_PAGINATION_CLASS="ninja_extra.pagination.LimitOffsetPagination"
export NINJA_PAGINATION_PER_PAGE=100
export MYPY_CACHE_DIR="$HOME/.cache/mypy"
export NUMBA_CACHE_DIR="$HOME/.cache/numba"
export PIP_CERT="/etc/ssl/certs/ca-certificates.crt"
export PIP_DEFAULT_TIMEOUT=100
export PIP_DISABLE_PIP_VERSION_CHECK=1
export PIP_INDEX_URL="https://pypi.org/simple/"
export PIP_NO_BUILD_ISOLATION=0
export PIP_NO_CACHE_DIR=1
export PIP_PROGRESS_BAR="on"
export PIP_RESPECT_VENV_ENV=false
export PIP_REQUIRE_HASHES=false
export PIP_REQUIRE_VIRTUALENV=false
export POETRY_CACHE_DIR="$HOME/.cache/poetry"
export POETRY_HOME="$HOME/.local/share/poetry"
export POETRY_VENV_IN_PROJECT=true
export PRE_COMMIT_HOME="$HOME/.cache/pre-commit"
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
# eval "$(pyenv virtualenv-init -)"
export PYTEST_CACHE_DIR="$HOME/.cache/pytest"
export PYTHON="python3"
export PYTHONBREAKPOINT="pdb.set_trace"
export PYTHONFAULTHANDLER="1"
export PYTHONHASHSEED="random"
export PYTHONIOENCODING="utf-8"
export PYTHONOPTIMIZE=1
export PYTHONSTARTUP="$HOME/.config/pythonrc.py"
export PYTHONUNBUFFERED=1
export PYTHONNOUSERSITE=1
export PYTHONWARNINGS="ignore::DeprecationWarning"
export REQUESTS_CA_BUNDLE="/etc/ssl/certs/ca-certificates.crt"
export SSL_CERT_FILE="/etc/ssl/certs/ca-certificates.crt"
export TORCH_HOME="$HOME/.cache/torch"
export VIRTUAL_ENV_DISABLE_PROMPT="1"
