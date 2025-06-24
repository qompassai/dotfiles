#!/bin/bash
# ~/qompassai/dotfiles/distro-hyprland.sh
# ------------------------------------------
# Copyright (C) 2025 Qompass AI, All rights reserved

OK="$(tput setaf 2)[OK]$(tput sgr0)"
ERROR="$(tput setaf 1)[ERROR]$(tput sgr0)"
NOTE="$(tput setaf 3)[NOTE]$(tput sgr0)"
INFO="$(tput setaf 4)[INFO]$(tput sgr0)"
WARN="$(tput setaf 1)[WARN]$(tput sgr0)"
CAT="$(tput setaf 6)[ACTION]$(tput sgr0)"
MAGENTA="$(tput setaf 5)"
ORANGE="$(tput setaf 214)"
WARNING="$(tput setaf 1)"
YELLOW="$(tput setaf 3)"
GREEN="$(tput setaf 2)"
BLUE="$(tput setaf 4)"
SKY_BLUE="$(tput setaf 6)"
RESET="$(tput sgr0)"

if [ -f /etc/os-release ]; then
    . /etc/os-release
    distro_name=$NAME
    distro_version=$VERSION_ID
else
    echo "${ERROR} Unable to detect the distribution. Exiting."
    exit 1
fi
if [ "$distro_name" = "Debian GNU/Linux" ]; then
    PACKAGE_MANAGER="apt"
    INSTALL_CMD="sudo apt install -y"
    GIT_INSTALL_CMD="sudo apt install -y git"
    Distro="debian"
    Github_URL="https://github.com/qompassai/$Distro.git"
    Distro_DIR="$HOME/$Distro"
elif [ "$distro_name" = "ubuntu" ]; then
    PACKAGE_MANAGER="apt"
    INSTALL_CMD="sudo apt install -y"
    GIT_INSTALL_CMD="sudo apt install -y git"

    case "$distro_version" in
        "24.04")
            Distro="ubuntu"
            Github_URL="https://github.com/qompassai/$Distro.git"
            Github_URL_branch="24.04"
            Distro_DIR="$HOME/$Distro-$Github_URL_branch"
            echo "${INFO} Ubuntu 24.04 detected. Customizing setup for Ubuntu 24.04."
            ;;
        "24.10")
            Distro="ubuntu"
            Github_URL="https://github.com/qompassai/$Distro.git"
            Github_URL_branch="24.10"
            Distro_DIR="$HOME/$Distro-$Github_URL_branch"
            echo "${INFO} Ubuntu 24.10 detected. Customizing setup for Ubuntu 24.10."
            ;;
        "25.04")
            Distro="ubuntu"
            Github_URL="https://github.com/qompassai/$Distro.git"
            Github_URL_branch="25.04"
            Distro_DIR="$HOME/$Distro-$Github_URL_branch"
            echo "${INFO} Ubuntu 25.04 detected. Customizing setup for Ubuntu 25.04."
            ;;
        *)
            Distro="ubuntu"
            echo "${ERROR} Unsupported distribution: $distro_version. Exiting."
            exit 1
            ;;
    esac

elif command -v pacman &> /dev/null; then
    PACKAGE_MANAGER="pacman"
    INSTALL_CMD="sudo pacman -S --noconfirm"
    GIT_INSTALL_CMD="sudo pacman -S git --noconfirm"
    Distro="arch"
    Github_URL="https://github.com/qompassai/$Distro.git"
    Distro_DIR="$HOME/$Distro"
elif command -v dnf &> /dev/null; then
    PACKAGE_MANAGER="dnf"
    INSTALL_CMD="sudo dnf install -y"
    GIT_INSTALL_CMD="sudo dnf install -y git"
    Distro="fedora"
    Github_URL="https://github.com/qompassai/$Distro.git"
    Distro_DIR="$HOME/$Distro"
elif command -v zypper &> /dev/null; then
    PACKAGE_MANAGER="zypper"
    INSTALL_CMD="sudo zypper install -y"
    GIT_INSTALL_CMD="sudo zypper install -y git"
    Distro="opensuse"
    Github_URL="https://github.com/qompassai/$Distro.git"
    Distro_DIR="$HOME/$Distro"
elif [ "$distro_name" = "NixOS" ]; then
    PACKAGE_MANAGER="nix"
    INSTALL_CMD="nix-shell"
    GIT_INSTALL_CMD="nix-shell -p git curl pciutils"
    Distro="nix"
    Github_URL="https://github.com/qompassai/$Distro.git"
    Distro_DIR="$HOME/$Distro"
else
    echo "${ERROR} Unsupported distribution: $distro_name. Exiting."
    exit 1
fi

if ! command -v git &> /dev/null; then
    echo "${INFO} Git not found! ${SKY_BLUE}Installing Git...${RESET}"
    if ! $GIT_INSTALL_CMD; then
        echo "${ERROR} Failed to install Git. Exiting."
        exit 1
    fi
fi

if [ -d "$Distro_DIR" ]; then
    echo "${YELLOW}$Distro_DIR exists. Updating the repository... ${RESET}"
    cd "$Distro_DIR"
    git stash && git pull
    chmod +x install.sh
    ./install.sh
else
    echo "${MAGENTA}$Distro_DIR does not exist. Cloning the repository...${RESET}"

    if [ "$distro_name" = "Ubuntu" ]; then
        echo "${INFO} Cloning from branch ${Github_URL_branch} for Ubuntu $distro_version."
        git clone --depth=1 -b "$Github_URL_branch" "$Github_URL" "$Distro_DIR"
    else
        git clone --depth=1 "$Github_URL" "$Distro_DIR"
    fi

    cd "$Distro_DIR"
    chmod +x install.sh
    ./install.sh
fi
