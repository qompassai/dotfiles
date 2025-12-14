#!/usr/bin/env bash
# /qompassai/Shell/.profile.d/52-js.sh
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################

# JavaScript environment paths
export BUN_INSTALL="${HOME}/.bun"
export DENO_INSTALL="${HOME}/.deno"
#export NODE_ENV="development"
export NVM_DIR="${HOME}/.config/nvm"
export YARN_CACHE_FOLDER="${HOME}/.cache/yarn"

path_add() {
  if [[ ":$PATH:" != *":$1:"* ]]; then
    export PATH="$1:${PATH}"
  fi
}

path_add "${BUN_INSTALL}/bin"
path_add "${DENO_INSTALL}/bin"
path_add "${PNPM_HOME}/bin"

if [[ -s "${NVM_DIR}/nvm.sh" ]]; then
  source "${NVM_DIR}/nvm.sh"
  [ -s "${NVM_DIR}/bash_completion" ] && source "${NVM_DIR}/bash_completion"
fi

jsproject() {
  local project_name="${1:-new-project}"
  mkdir -p "${project_name}" || return 1
  cd "${project_name}" || return 1

  # Initialize project
  if command -v npm >/dev/null; then
    npm init -y
  else
    echo "Error: npm not found. Please install Node.js first." >&2
    return 1
  fi

  # Create basic structure
  mkdir -p src tests docs
  echo "console.log('Hello World');" >src/index.js
  echo "# ${project_name}" >README.md

  # Create basic .gitignore
  if ! [[ -f .gitignore ]]; then
    cat >.gitignore <<EOF
node_modules/
*.log
.env
.DS_Store
EOF
  fi

  echo "Created JavaScript project: ${project_name}"
}

jsversions() {
  echo "=== JavaScript Versions ==="
  command -v node >/dev/null && echo "Node.js: $(node --version)"
  command -v npm >/dev/null && echo "npm: $(npm --version)"
  command -v yarn >/dev/null && echo "Yarn: $(yarn --version)"
  command -v pnpm >/dev/null && echo "pnpm: $(pnpm --version)"
  command -v bun >/dev/null && echo "Bun: $(bun --version)"
  command -v deno >/dev/null && echo "Deno: $(deno --version | head -n1)"
}

jsclean() {
  echo "Cleaning caches..."
  command -v npm >/dev/null && npm cache clean --force
  command -v yarn >/dev/null && yarn cache clean
  command -v pnpm >/dev/null && pnpm store prune
  command -v bun >/dev/null && bun pm cache rm
  echo "Cleanup complete"
}

jsaudit() {
  if [ -f "package-lock.json" ]; then
    npm audit
  elif [ -f "yarn.lock" ]; then
    yarn audit
  elif [ -f "pnpm-lock.yaml" ]; then
    pnpm audit
  elif [ -f "bun.lockb" ]; then
    bun audit
  else
    echo "No lock file found"
    return 1
  fi
}

export -f jsproject jsversions jsclean jsaudit
