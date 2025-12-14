<!-- readme.md -->
<!-- Qompass AI - [Add description here] -->
<!-- Copyright (C) 2025 Qompass AI, All rights reserved -->
<!-- ---------------------------------------- -->
# Chromium-like options (set for wrapper scripts or reference)
incognito=true           # Start in incognito mode
disable_gpu=true         # Disable hardware acceleration
disable_plugins=true     # Disable plugins
proxy_server=socks5://localhost:1080    # Proxy server
allow_running_insecure_content=true     # Allow mixed content
disable_web_security=false              # Strict origin policy (set true to disable)
disk_cache_size=104857600              # 100MB browser cache
user_data_dir=${XDG_DATA_HOME:-$HOME/.local/share}/carbonyl

# Chromium/Carbonyl engine options (CLI only, for docs/launchers)
# --enable-blink-features=...           # Enable experimental Blink features
# --disable-background-timer-throttling # Prevent tab throttling
# --window-size=1200,800                # Render window size in pixels
# --disable-images                      # Disable image loading (if supported)

# Environment variables (for launchers/scripts)
# export XDG_CACHE_HOME="$HOME/.cache"
# export XDG_DATA_HOME="$HOME/.local/share"

# Notes:
# - Some options here are passed via CLI. For options not directly parsed by config,
#   add them to your Carbonyl launcher wrapper or manually at the terminal.
# - Environment variables ensure compatibility with XDG paths.
# - Adjust proxy, cache size, and rendering settings to match your workflow.

# End of config

