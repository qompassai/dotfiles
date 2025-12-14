if [[ $XDG_SESSION_DESKTOP == "Hyprland" || $XDG_CURRENT_DESKTOP == "Hyprland" ]]; then
    export CLUTTER_BACKEND=wayland
    export GDK_BACKEND=wayland
    export MOZ_ENABLE_WAYLAND=1
    export NO_AT_BRIDGE=1
    export QT_QPA_PLATFORM=wayland
    export QT_QPA_PLATFORMTHEME=xdgdesktopportal
    export SDL_VIDEODRIVER=wayland
    export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$HOME/.cache}"
    export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
    export XDG_CURRENT_DESKTOP=Hyprland
    export XDG_DATA_DIRS="$XDG_DATA_HOME:/usr/local/share:/usr/share:/var/lib/flatpak/exports/share:$HOME/.local/share/flatpak/exports/share"
    export XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
    export XDG_DESKTOP_DIR="$HOME/.Desktop"
    export XDG_DOCUMENTS_DIR="$HOME/.Documents"
    export XDG_DOWNLOAD_DIR="$HOME/.Downloads"
    export XDG_MENU_PREFIX=arch-
    export XDG_MUSIC_DIR="$HOME/.Music"
    export XDG_PICTURES_DIR="$HOME/.Pictures"
    export XDG_PUBLICSHARE_DIR="$HOME/.Public"
    export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
    export XDG_SESSION_DESKTOP=Hyprland
    export XDG_SESSION_TYPE=wayland
    export XDG_STATE_HOME="${XDG_STATE_HOME:-$HOME/.local/state}"
    export XDG_TEMPLATES_DIR="$HOME/.Templates"
    export XDG_VIDEOS_DIR="$HOME/.Videos"
fi
