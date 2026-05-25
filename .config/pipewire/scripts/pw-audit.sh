#!/usr/bin/env bash
# /qompassai/dotfiles/.config/pipewire/scripts/pw-audit.sh
# Qompass AI Pipewire Audit Script
# Copyright (C) 2026 Qompass AI, All rights reserved
##########################################################
set -euo pipefail
ALSA_UCM_PKG="alsa-ucm-conf"
FILTER_NODES=(
    effect_input.eq6
    effect_input.rnnoise
    effect_input.virtual-surround-5.1-kemar
)
FILTER_NAMES=(eq6 rnnoise virtual-surround)
FULL=false
GRAPH=false
PROFILE_SECS=5
XDG_CACHE_HOME="${XDG_CACHE_HOME:-$HOME/.cache}"
XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
XDG_STATE_HOME="${XDG_STATE_HOME:-$HOME/.local/state}"
PW_CONFIG_DIR="$XDG_CONFIG_HOME/pipewire"
PW_DATA_DIR="$XDG_DATA_HOME/pipewire"
PW_RUNTIME_DIR="$XDG_RUNTIME_DIR/pipewire"
PW_STATE_DIR="$XDG_STATE_HOME/wireplumber"
WP_CONFIG_DIR="$XDG_CONFIG_HOME/wireplumber"
RNNOISE_PATH="/usr/lib/ladspa/librnnoise_ladspa.so"
REPORT_DIR="$XDG_STATE_HOME/pw-audit"
SOF_CODEC_PATH="/proc/asound/card2/codec#0"
SOF_NHLT_PATH="/var/lib/alsa/card2.conf.d/dmics-nhlt.json"
SOF_PKG="sof-firmware"
SPA_DIRS=(/usr/lib/spa-0.2 /usr/lib64/spa-0.2)
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
OUT="$REPORT_DIR/$TIMESTAMP"
while [[ $# -gt 0 ]]; do
    case $1 in
        --full) FULL=true ;;
        --graph) GRAPH=true ;;
        --profile)
            PROFILE_SECS="${2:-5}"
            [[ $PROFILE_SECS =~ ^[0-9]+$ ]] \
                || {
                    printf 'error: --profile requires a positive integer\n' >&2
                    exit 1
                }
            shift
            ;;
        -h | --help)
            cat << EOF
Usage: $0 [--full] [--graph] [--profile <seconds>]
  --full      Include spa-inspect for all SPA plugins
  --graph     Render graph.svg via pw-dot + graphviz
  --profile N Run pw-profiler for N seconds (default: 5)
EOF
            exit 0
            ;;
        *)
            printf 'error: unknown option: %s\n' "$1" >&2
            exit 1
            ;;
    esac
    shift
done
mkdir -p "$OUT"
REPORT="$OUT/pw-audit-report.md"

r()
{
    printf '%s\n' "$*" >> "$REPORT"
}
rh()
{
    printf '\n## %s\n\n' "$*" >> "$REPORT"
}
rl()
{
    printf -- '- **%s**: %s\n' "$1" "$2" >> "$REPORT"
}
rr()
{
    printf '```\n' >> "$REPORT"
    "$@" >> "$REPORT" 2>&1 || true
    printf '```\n' >> "$REPORT"
}
require()
{
    command -v "$1" &> /dev/null
}
trap 'printf "\n\n---\n⚠️ Audit interrupted at %s\n" "$(date)" >> "$REPORT"' ERR
{
    printf '# PipeWire Audit Report\n\n' > "$REPORT"
    printf '| Field | Value |\n|---|---|\n' >> "$REPORT"
}
rl "Full mode" "$FULL"
rl "Generated" "$(date)"
rl "Graph mode" "$GRAPH"
rl "Host" "$(hostname)"
rl "Kernel" "$(uname -r)"
rl "Output dir" "$OUT"
rl "Profile sec" "$PROFILE_SECS"
rl "User" "$(whoami)"
rl "XDG_CACHE_HOME" "$XDG_CACHE_HOME"
rl "XDG_CONFIG_HOME" "$XDG_CONFIG_HOME"
rl "XDG_DATA_HOME" "$XDG_DATA_HOME"
rl "XDG_RUNTIME_DIR" "$XDG_RUNTIME_DIR"
rl "XDG_STATE_HOME" "$XDG_STATE_HOME"
rh "1. ALC274 / SOF Hardware Check"
if [[ -f $SOF_CODEC_PATH ]]; then
    rl "SOF HDA DSP (card2)" "✅ present"
    {
        printf '```\n' >> "$REPORT"
        grep "Codec:" /proc/asound/card*/codec#* 2> /dev/null >> "$REPORT" || true
        printf '```\n' >> "$REPORT"
    }
else
    rl "SOF HDA DSP (card2)" "❌ not found — check: dmesg | grep -i sof"
fi
if pacman -Q "$SOF_PKG" &> /dev/null; then
    rl "$SOF_PKG" "✅ $(pacman -Q "$SOF_PKG" | awk '{print $2}')"
else
    rl "$SOF_PKG" "❌ not installed — sudo pacman -S $SOF_PKG"
fi
if pacman -Q "$ALSA_UCM_PKG" &> /dev/null; then
    rl "$ALSA_UCM_PKG" "✅ $(pacman -Q "$ALSA_UCM_PKG" | awk '{print $2}')"
else
    rl "$ALSA_UCM_PKG" "❌ not installed — sudo pacman -S $ALSA_UCM_PKG"
fi
if [[ -f $RNNOISE_PATH ]]; then
    rl "RNNoise LADSPA" "✅ $RNNOISE_PATH"
else
    rl "RNNoise LADSPA" "❌ missing — sudo pacman -S noise-suppression-for-voice"
fi
rh "2. Config Merge (pw-config)"
if require pw-config; then
    for conf in filter-chain.conf pipewire-pulse.conf pipewire.conf; do
        r "### $conf"
        rr pw-config -n "$conf" dump
    done
else
    r "❌ pw-config not found"
fi
rh "3. Config Files (XDG)"
r "### PipeWire drop-ins: $PW_CONFIG_DIR"
if [[ -d $PW_CONFIG_DIR ]]; then
    {
        printf '```\n' >> "$REPORT"
        find "$PW_CONFIG_DIR" -type f | sort >> "$REPORT"
        printf '```\n' >> "$REPORT"
    }
    for f in "$PW_CONFIG_DIR"/**/*.conf "$PW_CONFIG_DIR"/*.conf; do
        [[ -f $f ]] || continue
        r "#### $(basename "$f")"
        rr cat "$f"
    done
else
    r "❌ not found: $PW_CONFIG_DIR"
fi
r ""
r "### WirePlumber drop-ins: $WP_CONFIG_DIR"
if [[ -d $WP_CONFIG_DIR ]]; then
    {
        printf '```\n' >> "$REPORT"
        find "$WP_CONFIG_DIR" -type f | sort >> "$REPORT"
        printf '```\n' >> "$REPORT"
    }
    for f in "$WP_CONFIG_DIR"/**/*.conf "$WP_CONFIG_DIR"/**/*.lua "$WP_CONFIG_DIR"/*.conf; do
        [[ -f $f ]] || continue
        r "#### $(basename "$f")"
        rr cat "$f"
    done
else
    r "❌ not found: $WP_CONFIG_DIR"
fi
r ""
r "### PipeWire data: $PW_DATA_DIR"
if [[ -d $PW_DATA_DIR ]]; then
    {
        printf '```\n' >> "$REPORT"
        find "$PW_DATA_DIR" -type f | sort >> "$REPORT"
        printf '```\n' >> "$REPORT"
    }
else
    r "not present"
fi
r ""
r "### WirePlumber state: $PW_STATE_DIR"
if [[ -d $PW_STATE_DIR ]]; then
    {
        printf '```\n' >> "$REPORT"
        find "$PW_STATE_DIR" -type f | sort >> "$REPORT"
        printf '```\n' >> "$REPORT"
    }
else
    r "not present"
fi
r ""
r "### Runtime sockets: $PW_RUNTIME_DIR"
if [[ -d $PW_RUNTIME_DIR ]]; then
    {
        printf '```\n' >> "$REPORT"
        ls -la "$PW_RUNTIME_DIR" 2> /dev/null >> "$REPORT" || true
        printf '```\n' >> "$REPORT"
    }
else
    r "not present"
fi
rh "4. Daemon Health"
for svc in pipewire pipewire-pulse wireplumber; do
    if systemctl --user is-active --quiet "$svc"; then
        rl "$svc" "✅ running"
    else
        rl "$svc" "❌ NOT running"
        {
            printf '```\n' >> "$REPORT"
            systemctl --user status "$svc" --no-pager -l 2>&1 | head -20 >> "$REPORT" || true
            printf '```\n' >> "$REPORT"
        }
    fi
done
rh "5. Device Info (pw-cli)"
if require pw-cli; then
    r "### Core info"
    rr pw-cli info 0
    r "### Object list"
    {
        pw-cli list-objects > "$OUT/pw-cli-list.txt" 2>&1 || true
        printf '```\n' >> "$REPORT"
        cat "$OUT/pw-cli-list.txt" >> "$REPORT"
        printf '```\n' >> "$REPORT"
    }
fi
rh "6. Device Reservation (pw-reserve)"
if require pw-reserve; then
    for dev in Audio0 Audio1; do
        if pw-reserve -c "pw-audit" "$dev" > /dev/null 2>&1; then
            rl "$dev" "✅ free — no exclusive reservation held"
        else
            rl "$dev" "⚠️  reserved by another process"
        fi
    done
fi

rh "7. DSP Profiler (pw-profiler)"
if require pw-profiler; then
    PROF_OUT="$OUT/pw-profiler.log"
    {
        timeout "$PROFILE_SECS" pw-profiler > "$PROF_OUT"
    } 2>&1 || true
    XRUNS=$(grep -c -i "xrun\|underrun\|overrun" "$PROF_OUT" 2> /dev/null || printf '0')
    rl "Duration" "${PROFILE_SECS}s"
    rl "Full log" "$PROF_OUT"
    if [[ $XRUNS -gt 0 ]]; then
        rl "Xrun events" "⚠️  $XRUNS — reduce load or increase quantum"
    else
        rl "Xrun events" "✅ 0"
    fi
    r ""
    r "### Profiler output (first 60 lines)"
    {
        printf '```\n' >> "$REPORT"
        head -60 "$PROF_OUT" >> "$REPORT" 2> /dev/null || true
        printf '```\n' >> "$REPORT"
    }
fi
rh "8. Graph Dump (pw-dump)"
if require pw-dump; then
    pw-dump 2> /dev/null > "$OUT/pw-dump.json"
    NODE_COUNT=$(jq '[.[] | select(.type == "PipeWire:Interface:Node")] | length' \
        "$OUT/pw-dump.json" 2> /dev/null || printf '?')
    LINK_COUNT=$(jq '[.[] | select(.type == "PipeWire:Interface:Link")] | length' \
        "$OUT/pw-dump.json" 2> /dev/null || printf '?')
    rl "Raw JSON" "$OUT/pw-dump.json (pipe to jq for filtering)"
    rl "Total links" "$LINK_COUNT"
    rl "Total nodes" "$NODE_COUNT"
    r ""
    r "### All node names"
    {
        printf '```\n' >> "$REPORT"
        jq -r '.[] | select(.type == "PipeWire:Interface:Node") | .info.props["node.name"] // "(unnamed)"' \
            "$OUT/pw-dump.json" 2> /dev/null | sort >> "$REPORT"
        printf '```\n' >> "$REPORT"
    }
    jq -r '.[] | select(.type == "PipeWire:Interface:Node") | .info.props["node.name"] // ""' \
        "$OUT/pw-dump.json" 2> /dev/null | sort > "$OUT/node-names.txt"
    r ""
    r "### Expected filter nodes"
    for node in "${FILTER_NODES[@]}"; do
        if grep -q "$node" "$OUT/node-names.txt"; then
            rl "$node" "✅ present"
        else
            rl "$node" "⚠️  missing"
        fi
    done
fi
rh "9. Graph Visualization (pw-dot)"
if require pw-dot; then
    pw-dot 2> /dev/null > "$OUT/graph.dot"
    rl "DOT file" "$OUT/graph.dot"
    if [[ $GRAPH == true ]]; then
        if require dot; then
            dot -Tsvg "$OUT/graph.dot" > "$OUT/graph.svg" 2> /dev/null
            rl "SVG render" "✅ $OUT/graph.svg"
        else
            rl "SVG render" "❌ graphviz not installed — sudo pacman -S graphviz"
        fi
    else
        rl "SVG render" "skipped — rerun with --graph to generate"
    fi
fi
rh "10. Metadata (pw-metadata)"
if require pw-metadata; then
    r "### Default node assignments"
    {
        printf '```\n' >> "$REPORT"
        pw-metadata 0 2> /dev/null | grep -E "default|clock" >> "$REPORT" \
            || printf '(none)\n' >> "$REPORT"
        printf '```\n' >> "$REPORT"
    }
    rr pw-metadata -n filters
    rr pw-metadata -n settings
fi

rh "11. Active Port Links (pw-link)"
if require pw-link; then
    {
        pw-link -l > "$OUT/pw-links.txt" 2>&1 || true
        pw-link -i >> "$OUT/pw-links.txt" 2>&1 || true
        pw-link -o >> "$OUT/pw-links.txt" 2>&1 || true
    }
    {
        printf '```\n' >> "$REPORT"
        pw-link -l >> "$REPORT" 2>&1 || true
        printf '```\n' >> "$REPORT"
    }
    {
        printf '```\n' >> "$REPORT"
        pw-link -i >> "$REPORT" 2>&1 || true
        printf '```\n' >> "$REPORT"
    }
    {
        printf '```\n' >> "$REPORT"
        pw-link -o >> "$REPORT" 2>&1 || true
        printf '```\n' >> "$REPORT"
    }
fi
rh "12. SPA Layer"
if [[ -f $SOF_NHLT_PATH ]]; then
    if require spa-json-dump; then
        if spa-json-dump "$SOF_NHLT_PATH" > "$OUT/dmics-nhlt-dump.txt" 2>&1; then
            rl "DMIC NHLT blob" "✅ parsed OK — $OUT/dmics-nhlt-dump.txt"
        else
            rl "DMIC NHLT blob" "❌ parse failed — DMIC capture may be broken"
        fi
    fi
else
    rl "DMIC NHLT blob" "❌ not found at $SOF_NHLT_PATH — run: sudo alsactl init"
fi
if require spa-monitor; then
    {
        printf '```\n' >> "$REPORT"
        timeout 1 spa-monitor api.alsa.enum.udev >> "$REPORT" 2>&1 || true
        printf '```\n' >> "$REPORT"
    }
fi
if [[ $FULL == true ]] && require spa-inspect; then
    r ""
    r "### SPA plugin inventory (--full)"
    for dir in "${SPA_DIRS[@]}"; do
        [[ -d $dir ]] || continue
        while IFS= read -r so; do
            plugin=$(basename "$so" .so)
            printf '#### %s\n```\n' "$plugin" >> "$REPORT"
            spa-inspect "$so" >> "$OUT/spa-inspect.txt" 2>&1 || true
            head -20 "$OUT/spa-inspect.txt" >> "$REPORT" 2> /dev/null || true
            printf '```\n' >> "$REPORT"
        done < <(find "$dir" -name "*.so" | sort)
    done
fi
rh "13. WirePlumber Status (wpctl)"
if require wpctl; then
    WPCTL_OUT=$(wpctl status 2> /dev/null || true)
    printf '%s\n' "$WPCTL_OUT" > "$OUT/wpctl-status.txt"
    r "### Graph overview"
    {
        printf '```\n' >> "$REPORT"
        cat "$OUT/wpctl-status.txt" >> "$REPORT"
        printf '```\n' >> "$REPORT"
    }
    r ""
    NULL_COUNT=$(printf '%s\n' "$WPCTL_OUT" | grep -c "(null)" || true)
    if [[ $NULL_COUNT -gt 0 ]]; then
        rl "Null nodes" "⚠️  $NULL_COUNT detected — orphaned filter outputs, run: pipewire -c filter-chain.conf"
    else
        rl "Null nodes" "✅ none"
    fi
    for name in "${FILTER_NAMES[@]}"; do
        if printf '%s\n' "$WPCTL_OUT" | grep -q "$name"; then
            rl "Filter: $name" "✅ active"
        else
            rl "Filter: $name" "⚠️  not found — filter-chain.conf may not be loaded"
        fi
    done
fi
rh "14. File Index"
r ""
r "| File | Contents |"
r "|---|---|"
r '| `dmics-nhlt-dump.txt` | DMIC NHLT ACPI blob (if present) |'
r '| `graph.dot`           | Graphviz DOT graph topology |'
r '| `node-names.txt`      | Sorted node name list for smart filter targeting |'
r '| `pw-audit-report.md`  | This report |'
r '| `pw-cli-list.txt`     | All PipeWire interface objects |'
r '| `pw-dump.json`        | Full graph JSON — pipe to jq |'
r '| `pw-links.txt`        | All active port link connections |'
r '| `pw-profiler.log`     | DSP cycle timing and xrun events |'
r '| `wpctl-status.txt`    | WirePlumber graph overview |'
[[ $GRAPH == true ]] && r '| `graph.svg`           | Rendered graph visualization |'
[[ $FULL == true ]] && r '| `spa-inspect.txt`     | Full SPA plugin inventory |'
r ""
r "---"
r '_Run `pw-top` interactively to monitor live DSP CPU usage per node._'
r '_Rerun with `--full --graph --profile 10` for a complete audit._'
printf '%s\n' "$REPORT"
