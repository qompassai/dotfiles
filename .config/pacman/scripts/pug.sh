#!/usr/bin/env bash
# pug.sh
# Qompass AI - Package Update Gist
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
PUG_CONFIG_DIR="${XDG_CONFIG_HOME}/pacman"
PUG_CONFIG_FILE="${PUG_CONFIG_DIR}/pug.conf"
PUG_SCRIPTS_DIR="${PUG_CONFIG_DIR}/scripts"
normal="$(tput sgr0)"
bold="$(tput bold)"
red="$(tput setaf 1)"
green="$(tput setaf 2)"
cyan="$(tput setaf 6)"
white="$(tput setaf 7)"
PACMANFILE="$(hostname).pacman-list.pkg"
AURFILE="$(hostname).aur-list.pkg"
mkdir -p "${PUG_CONFIG_DIR}" "${PUG_SCRIPTS_DIR}"
pug_install()
{
    echo "${bold}${green}==>${white} Checking GitHub authentication..."
    if ! gh auth status &> /dev/null; then
        echo "${bold}${red}::${white} Not authenticated with GitHub CLI.${normal}"
        echo "${bold}${cyan}::${white} Run: gh auth login${normal}"
        exit 1
    fi

    echo "${bold}${green}==>${white} Saving installed package lists to gists..."
    echo "${bold}${cyan}  ->${white} Creating package lists..."

    TEMP_DIR=$(mktemp -d)
    trap 'rm -rf "${TEMP_DIR}"' EXIT

    pacman -Qqen > "${TEMP_DIR}/${PACMANFILE}"
    pacman -Qqem > "${TEMP_DIR}/${AURFILE}"

    echo "${bold}${cyan}  ->${white} Creating gists..."
    GIST_NAT_URL=$(gh gist create "${TEMP_DIR}/${PACMANFILE}" \
        --desc "Pacman package list for $(hostname)" \
        --public)
    GIST_AUR_URL=$(gh gist create "${TEMP_DIR}/${AURFILE}" \
        --desc "AUR package list for $(hostname)" \
        --public)
    if [ -z "${GIST_NAT_URL}" ] || [ -z "${GIST_AUR_URL}" ]; then
        echo "${bold}${red}::${white} Failed to create gists.${normal}"
        exit 1
    fi
    GIST_NAT="${GIST_NAT_URL##*/}"
    GIST_AUR="${GIST_AUR_URL##*/}"
    cat > "${PUG_CONFIG_FILE}" << EOF
GIST_NAT=${GIST_NAT}
GIST_AUR=${GIST_AUR}
EOF

    echo "    [ ${cyan}${GIST_NAT_URL}${white} ]"
    echo "    [ ${cyan}${GIST_AUR_URL}${white} ]"
    echo "${bold}${green}==>${white} Configuration saved to ${PUG_CONFIG_FILE}${normal}"
}
pug_update()
{
    echo "${bold}${cyan}::${white} Processing gists update...${normal}"
    # shellcheck source=/dev/null
    if [ -f "${PUG_CONFIG_FILE}" ]; then
        source "${PUG_CONFIG_FILE}"
    elif [ -f "${PUG_CONFIG_FILE}.bkp" ]; then
        echo "${bold}${cyan}::${white} Loading backup configuration...${normal}"
        cp "${PUG_CONFIG_FILE}.bkp" "${PUG_CONFIG_FILE}"
        # shellcheck source=/dev/null
        source "${PUG_CONFIG_FILE}"
    else
        echo "${bold}${red}::${white} ${PUG_CONFIG_FILE}: gist IDs file not found.${normal}"
        echo "${bold}${red}::${white} Run 'pug install' first.${normal}"
        exit 1
    fi
    if ! gh auth status &> /dev/null; then
        echo "${bold}${red}::${white} Not authenticated with GitHub CLI.${normal}"
        echo "${bold}${cyan}::${white} Run: gh auth login${normal}"
        exit 1
    fi
    cp "${PUG_CONFIG_FILE}" "${PUG_CONFIG_FILE}.bkp"
    TEMP_DIR=$(mktemp -d)
    trap 'rm -rf "${TEMP_DIR}"' EXIT
    if ! gh gist view "${GIST_NAT}" --raw > "${TEMP_DIR}/pacman.gist" 2> /dev/null; then
        echo "${bold}${red}::${white} Failed to read pacman gist.${normal}"
        exit 1
    fi
    pacman -Qqen > "${TEMP_DIR}/pacman.list"
    if ! diff "${TEMP_DIR}/pacman.gist" "${TEMP_DIR}/pacman.list" > /dev/null 2>&1; then
        echo "${bold}${cyan}::${white} Updating pacman package list...${normal}"
        if ! gh gist edit "${GIST_NAT}" "${TEMP_DIR}/pacman.list" --filename "${PACMANFILE}"; then
            echo "${bold}${red}::${white} Failed to update pacman gist.${normal}"
            exit 1
        fi
        echo "${bold}${green}==>${white} Pacman list updated.${normal}"
    else
        echo "${bold}${cyan}::${white} Pacman list unchanged.${normal}"
    fi
    if ! gh gist view "${GIST_AUR}" --raw > "${TEMP_DIR}/aur.gist" 2> /dev/null; then
        echo "${bold}${red}::${white} Failed to read AUR gist.${normal}"
        exit 1
    fi
    pacman -Qqem > "${TEMP_DIR}/aur.list"
    if ! diff "${TEMP_DIR}/aur.gist" "${TEMP_DIR}/aur.list" > /dev/null 2>&1; then
        echo "${bold}${cyan}::${white} Updating AUR package list...${normal}"
        if ! gh gist edit "${GIST_AUR}" "${TEMP_DIR}/aur.list" --filename "${AURFILE}"; then
            echo "${bold}${red}::${white} Failed to update AUR gist.${normal}"
            exit 1
        fi
        echo "${bold}${green}==>${white} AUR list updated.${normal}"
    else
        echo "${bold}${cyan}::${white} AUR list unchanged.${normal}"
    fi
}
pug_main()
{
    if ! command -v gh &> /dev/null; then
        echo "${bold}${red}::${white} 'gh' command not found. Install it with: pacman -S github-cli${normal}"
        exit 1
    fi
    if [ -f "${PUG_CONFIG_FILE}" ]; then
        source "${PUG_CONFIG_FILE}"
    fi
    case "${1}" in
        install)
            pug_install
            ;;
        update)
            pug_update
            ;;
        *)
            if [ -z "${GIST_NAT}" ] || [ -z "${GIST_AUR}" ]; then
                echo "${bold}${cyan}::${white} Pug: fresh install needed.${normal}"
                pug_install
            else
                pug_update
            fi
            ;;
    esac
}
pug_main "$@"
