#!/usr/bin/env bash
# /qompassai/dotfiles/.config/pacman/list-systemd-units.sh
# Qompass AI Pacman Service List Script
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
set -Eeo pipefail
colorize()
{
    if tput setaf 0 &> /dev/null; then
        ALL_OFF="$(tput sgr0)"
        BOLD="$(tput bold)"
        BLUE="${BOLD}$(tput setaf 4)"
        GREEN="${BOLD}$(tput setaf 2)"
        RED="${BOLD}$(tput setaf 1)"
        YELLOW="${BOLD}$(tput setaf 3)"
    else
        ALL_OFF='\e[0m'
        BOLD='\e[1m'
        BLUE="${BOLD}\e[34m"
        GREEN="${BOLD}\e[32m"
        RED="${BOLD}\e[31m"
        YELLOW="${BOLD}\e[33m"
    fi
    readonly ALL_OFF BOLD BLUE GREEN RED YELLOW
}
ask()
{
    local mesg=$1
    shift
    printf '%s::%s%s %s%s' "${BLUE}" "${ALL_OFF}" "${BOLD}" "${mesg}" "${ALL_OFF}" "$@"
}
error()
{
    local mesg=$1
    shift
    printf '%s==> ERROR:%s%s %s%s\n' "${RED}" "${ALL_OFF}" "${BOLD}" "${mesg}" "${ALL_OFF}" "$@" >&2
}
msg()
{
    ((QUIET)) && return
    local mesg=$1
    shift
    printf '%s==>%s%s %s%s\n' "${GREEN}" "${ALL_OFF}" "${BOLD}" "${mesg}" "${ALL_OFF}" "$@"
}
msg2()
{
    ((QUIET)) && return
    local mesg=$1
    shift
    printf '%s  ->%s%s %s%s\n' "${BLUE}" "${ALL_OFF}" "${BOLD}" "${mesg}" "${ALL_OFF}" "$@"
}
plain()
{
    ((QUIET)) && return
    local mesg=$1
    shift
    printf '%s    %s%s\n' "${BOLD}" "${mesg}" "${ALL_OFF}" "$@"
}
plainerr()
{
    plain "$@" >&2
}
warning()
{
    local mesg=$1
    shift
    printf '%s==> WARNING:%s%s %s%s\n' "${YELLOW}" "${ALL_OFF}" "${BOLD}" "${mesg}" "${ALL_OFF}" "$@" >&2
}
colorize
declare -A package_units
declare -a unit_files
UNIT_DIRS=(
    "/etc/systemd/system"
    "/usr/lib/systemd/system"
    "/usr/share/systemd/system"
)
UNIT_TYPES=(
    "*.automount"
    "*.mount"
    "*.path"
    "*.service"
    "*.slice"
    "*.socket"
    "*.swap"
    "*.target"
    "*.timer"
)
find_args=()
for type in "${UNIT_TYPES[@]}"; do
    [[ ${#find_args[@]} -gt 0 ]] && find_args+=(-o)
    find_args+=(-name "${type}")
done
msg "Scanning for systemd units..."
while IFS= read -r -d '' file; do
    unit_files+=("${file}")
done < <(find "${UNIT_DIRS[@]}" -type f \( "${find_args[@]}" \) -print0 2> /dev/null)
if [[ ${#unit_files[@]} -eq 0 ]]; then
    error "No systemd unit files found"
    exit 1
fi
msg2 "Found ${#unit_files[@]} unit files"
msg "Querying package ownership..."
while IFS=' ' read -r _ _ _ _ pkg file; do
    [[ -z ${pkg} || -z ${file} ]] && continue
    unit_name="${file##*/}"
    package_units["${pkg}"]+=" ${unit_name}"
done < <(env LANG=C pacman -Qo "${unit_files[@]}" 2> /dev/null)
if [[ ${#package_units[@]} -eq 0 ]]; then
    warning "No packages own the found unit files"
    exit 0
fi
msg2 "Found ${#package_units[@]} packages owning units"
echo
mapfile -t sorted_packages < <(printf '%s\n' "${!package_units[@]}" | sort)
first_package=true
for package in "${sorted_packages[@]}"; do
    if [[ ${first_package} == "true" ]]; then
        first_package=false
    else
        echo
    fi
    msg "${package}:"
    read -ra units <<< "${package_units[${package}]}"
    mapfile -t sorted_units < <(printf '%s\n' "${units[@]}" | sort)
    for unit in "${sorted_units[@]}"; do
        msg2 "${unit}"
    done
done
