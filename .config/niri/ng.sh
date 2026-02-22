#!/usr/bin/env bash
# /qompassai/dotfiles/.config/niri/ng.sh
# Qompass AI Niri Gen Script
# Copyright (C) 2025 Qompass AI, All rights reserved
###################################################
set -euo pipefail
SOURCES=(
    "$XDG_CONFIG_HOME/niri/autostart.kdl"
    "$XDG_CONFIG_HOME/niri/bindings.kdl"
    "$XDG_CONFIG_HOME/niri/input.kdl"
    "$XDG_CONFIG_HOME/niri/layout.kdl"
    "$XDG_CONFIG_HOME/niri/windows.kdl"
    "$XDG_CONFIG_HOME/niri/workspaces.kdl"
)
OUTPUT_PATH="$XDG_CONFIG_HOME/niri/config.kdl"
show_help()
{
    cat << 'HELP'
HELP
}
check_files()
{
    local missing_files=()
    for source in "${SOURCES[@]}"; do
        if [[ ! -f $source ]]; then
            missing_files+=("$source")
        fi
    done
    if [[ ${#missing_files[@]} -gt 0 ]]; then
        printf '%s\n' "${missing_files[@]}" >&2
        return 1
    fi
    print_info "All source files found ✓"
    return 0
}
validate_config()
{
    if [[ ! -f $OUTPUT_PATH ]]; then
        print_error "Config file does not exist: $OUTPUT_PATH"
        return 1
    fi
    if niri validate --config "$OUTPUT_PATH" > /dev/null 2>&1; then
        print_info "Configuration validation passed ✓"
        return 0
    else
        print_error "Configuration validation FAILED!"
        print_error "Running niri validate to show errors:"
        echo ""
        niri validate --config "$OUTPUT_PATH" || true
        echo ""
        print_error "Please check the source files for syntax errors"
        return 1
    fi
}
write_warning_header()
{
    local temp_file="$1"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    cat >> "$temp_file" << EOF
EOF
}
generate_config()
{
    if ! check_files; then
        exit 1
    fi
    mkdir -p "$(dirname "$OUTPUT_PATH")"
    local temp_file
    temp_file="$(mktemp "${OUTPUT_PATH}.XXXXXX")"
    write_warning_header "$temp_file"
    for source in "${SOURCES[@]}"; do
        print_info "Including: $source"
        cat "$source" >> "$temp_file"
        echo "" >> "$temp_file"
    done
    mv "$temp_file" "$OUTPUT_PATH"
    if ! validate_config; then
        print_error "Generated config is invalid! Exiting."
        exit 1
    fi
    print_info "✅ Config generated and validated successfully!"
}
case "${1:-generate}" in
    "generate" | "gen")
        generate_config
        ;;
    "check")
        check_files
        ;;
    "validate")
        validate_config
        ;;
    "help" | "-h" | "--help")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
