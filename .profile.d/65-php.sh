#!/usr/bin/env bash
# /qompassai/Shell/.profile.d/65-php.sh
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################

export COMPOSER_CACHE_DIR="$HOME/.cache/composer"
export COMPOSER_CONFIG_DIR="$HOME/.config/composer"
export PHP_CONFIG_DIR="$HOME/.config/php"
export PHP_EXT_DIR="$HOME/.php/extensions"
export PHP_INI_SCAN_DIR="$PHP_CONFIG_DIR"
export PHP_LOCAL_BIN="$HOME/.local/bin"
export PHP_VERSION=${PHP_VERSION:-"php"}
export PHPBREW_HOME="$HOME/.phpbrew"
export PHPBREW_ROOT="$HOME/.phpbrew"
export PATH="$PHP_LOCAL_BIN:$PATH"
export PATH="$HOME/.composer/vendor/bin:$PATH"
export PATH="$HOME/.config/composer/vendor/bin:$PATH"
export PATH="$HOME/.phpbrew/bin:$PATH"
export PATH="$HOME/.phpbrew/php/php-$PHP_VERSION/bin:$PATH"

if [ -f "$HOME/.composer/composer.phar" ]; then
    alias composer="php $HOME/.composer/composer.phar"
fi

phpaudit() {
    echo "=== PHP Security Audit ==="
    if [ -f "composer.lock" ]; then
        if command -v security-checker >/dev/null 2>&1; then
            security-checker security:check composer.lock
        else
            echo "Install security-checker with: composer global require sensiolabs/security-checker"
        fi
    else
        echo "No composer.lock found. Run from a PHP project directory."
    fi
}

phpclean() {
    echo "Cleaning PHP and Composer caches..."
    [ -d "$COMPOSER_CACHE_DIR" ] && rm -rf "$COMPOSER_CACHE_DIR"/*
    [ -d "$PHP_EXT_DIR" ] && rm -rf "$PHP_EXT_DIR"/*
    echo "Cache cleanup completed."
}

phpproject() {
    local project_name="${1:-new-php-project}"
    mkdir -p "$project_name"
    cd "$project_name" || return 1
    composer init --no-interaction
    echo "<?php\n\n// $project_name entry point\n" > index.php
    echo "# $project_name" > README.md
    echo "vendor/" > .gitignore
    echo "Created PHP project: $project_name"
}

phpversions() {
    echo "=== PHP Ecosystem Versions ==="
    command -v php >/dev/null && echo "PHP: $(php --version | head -1)"
    command -v composer >/dev/null && echo "Composer: $(composer --version | head -1)"
    command -v phpunit >/dev/null && echo "PHPUnit: $(phpunit --version 2>/dev/null | head -1)"
    command -v phpbrew >/dev/null && echo "phpbrew: $(phpbrew --version | head -1)"
    echo ""
    if command -v phpbrew >/dev/null; then
        echo "Installed PHP versions:"
        phpbrew list
    fi
}

export -f phpaudit phpclean phpproject phpversions

