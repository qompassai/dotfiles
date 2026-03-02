#!/usr/bin/env bash
# /qompassai/dotfiles/.config/pipewire/scripts/pw-val.sh
# Qompass AI PipeWire Config Validator
# Copyright (C) 2026 Qompass AI, All rights reserved
###########################################################################
set -uo pipefail
CONF_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/pipewire"
PASS=0
FAIL=0
WARN=0
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'
pass()
{
    echo -e "  ${GREEN}✔${RESET} $1"
    ((PASS++)) || true
}
fail()
{
    echo -e "  ${RED}✖${RESET} $1"
    ((FAIL++)) || true
}
warn()
{
    echo -e "  ${YELLOW}⚠${RESET} $1"
    ((WARN++)) || true
}
header()
{
    echo -e "\n${CYAN}${BOLD}── $1 ──${RESET}"
}
header "SPA-JSON Parse (pw-config)"
PW_CONFS=(
    "pipewire.conf"
    "pipewire-pulse.conf"
    "pipewire-alsa.conf"
)
for conf_name in "${PW_CONFS[@]}"; do
    conf_dir="$CONF_DIR/${conf_name%.conf}.conf.d"
    if [[ ! -d $conf_dir ]]; then
        warn "$conf_name — no .conf.d directory found, skipping"
        continue
    fi
    if pw-config -n "$conf_name" dump > /dev/null 2>&1; then
        pass "$conf_name parses without errors"
    else
        fail "$conf_name FAILED to parse:"
        pw-config -n "$conf_name" dump 2>&1 | sed 's/^/      /' || true
    fi
done
header "Per-file Checks"
shopt -s globstar nullglob
conf_files=("$CONF_DIR"/**/*.conf)

if [[ ${#conf_files[@]} -eq 0 ]]; then
    warn "No .conf files found under $CONF_DIR"
else
    for f in "${conf_files[@]}"; do
        rel="${f#"$CONF_DIR/"}"

        if grep -Pn ',\s*(\}|\])' "$f" > /dev/null 2>&1; then
            lines=$(grep -Pn ',\s*(\}|\])' "$f" | head -5 | sed 's/^/      /')
            fail "$rel — trailing comma(s):\n$lines"
        else
            pass "$rel — no trailing commas"
        fi

        if grep -Pn '"(true|false)"' "$f" > /dev/null 2>&1; then
            lines=$(grep -Pn '"(true|false)"' "$f" | head -5 | sed 's/^/      /')
            warn "$rel — quoted booleans (should be bare):\n$lines"
        fi

        if grep -Pn '=\s+"[0-9]+"' "$f" > /dev/null 2>&1; then
            lines=$(grep -Pn '=\s+"[0-9]+"' "$f" | head -5 | sed 's/^/      /')
            warn "$rel — quoted integers (should be bare):\n$lines"
        fi
        if grep -Pn '"[A-Z]{2}(,[A-Z]{2})+"' "$f" > /dev/null 2>&1; then
            lines=$(grep -Pn '"[A-Z]{2}(,[A-Z]{2})+"' "$f" | head -5 | sed 's/^/      /')
            fail "$rel — legacy comma-separated audio.position (use [ FL FR ]):\n$lines"
        fi

        if grep -Pn 'log\.level\s*=\s*[45]' "$f" > /dev/null 2>&1; then
            warn "$rel — log.level >= 4 active; performance impact in production"
        fi
        if grep -Pn '\[https?://' "$f" > /dev/null 2>&1; then
            lines=$(grep -Pn '\[https?://' "$f" | head -5 | sed 's/^/      /')
            fail "$rel — markdown link artifact (remove [ ] around URLs):\n$lines"
        fi
    done
fi
header "Runtime Dependencies"
bins=(pipewire pw-config pw-cli wireplumber pactl)
for b in "${bins[@]}"; do
    if command -v "$b" > /dev/null 2>&1; then
        ver=$("$b" --version 2> /dev/null | head -1 || echo "unknown")
        pass "$b — $ver"
    else
        warn "$b not found in PATH"
    fi
done
header "LV2 Plugin Check"
if command -v lv2ls > /dev/null 2>&1; then
    lv2_list=$(lv2ls 2> /dev/null)
    declare -A LV2_PLUGINS=(
        ["bankstown"]="https://chadmed.au/bankstown"
        ["loud_comp_mono"]="http://lsp-plug.in/plugins/lv2/loud_comp_mono"
        ["mb_compressor_stereo"]="http://lsp-plug.in/plugins/lv2/mb_compressor_stereo"
        ["compressor_stereo"]="http://lsp-plug.in/plugins/lv2/compressor_stereo"
    )
    for name in "${!LV2_PLUGINS[@]}"; do
        uri="${LV2_PLUGINS[$name]}"
        if echo "$lv2_list" | grep -qF "$uri"; then
            pass "LV2 $name"
        else
            fail "LV2 $name NOT FOUND — $uri"
        fi
    done
else
    warn "lv2ls not found (install lv2 package) — skipping LV2 checks"
fi
header "Convolver IR Files"
ir_files=(
    "/usr/share/pipewire/pipewire.conf.d/gpd-pocket-4-mp-48k-l.wav"
    "/usr/share/pipewire/pipewire.conf.d/gpd-pocket-4-mp-48k-r.wav"
)
for ir in "${ir_files[@]}"; do
    if [[ -f $ir ]]; then
        pass "$ir exists"
    else
        fail "$ir MISSING — convolver will fail to load"
    fi
done

header "Systemd Service State"
for svc in pipewire pipewire-pulse wireplumber; do
    state=$(systemctl --user is-active "$svc" 2> /dev/null || echo "unknown")
    case "$state" in
        active) pass "$svc is active" ;;
        inactive) warn "$svc is inactive" ;;
        failed) fail "$svc is FAILED" ;;
        *) warn "$svc state: $state" ;;
    esac
done
header "Network Interfaces (RTP/AVB/PTP)"
for iface in eth0 enp3s0; do
    if ip link show "$iface" > /dev/null 2>&1; then
        state=$(ip link show "$iface" | grep -oP '(?<=state )\S+')
        pass "$iface exists (state: $state)"
    else
        warn "$iface not found — rtp-sap/rtp-sink/avb will fail if bound here"
    fi
done
echo -e "\n${BOLD}────────────────────────────────${RESET}"
echo -e "  ${GREEN}✔ PASS${RESET}  $PASS"
echo -e "  ${YELLOW}⚠ WARN${RESET}  $WARN"
echo -e "  ${RED}✖ FAIL${RESET}  $FAIL"
echo -e "${BOLD}────────────────────────────────${RESET}"

[[ $FAIL -gt 0 ]] && exit 1 || exit 0
