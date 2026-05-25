#!/usr/bin/env bash
set -euo pipefail
# /qompassai/dotfiles/.config/pipewire/scripts/load_pw_modules.sh
# Qompass AI PipeWire Module Load Script
# Copyright (C) 2026 Qompass AI, All rights reserved
#################################################################
QUANTUMVAL=2048
QUANTUMVAL2=$((QUANTUMVAL * 2))
command -v pw-cli > /dev/null || {
    echo "pw-cli not found, exiting"
    exit 0
}
pw-cli quit 2> /dev/null || {
    echo "pipewire server is not running, exiting"
    exit 0
}
if [ -n "${XRDP_SESSION:-}" ] && [ -n "${XRDP_SOCKET_PATH:-}" ]; then
    OBJECT_IDS=$(
        pw-cli ls Node \
            | sed -e "s/^[^a-z]//" \
            | grep -w "^id" \
            | sed -e "s/^[^0-9]*//" -e "s/[^0-9]*/-/" \
            | cut -d- -f1
    )
    for OBJECT_ID in ${OBJECT_IDS}; do
        NODE_NAME=$(pw-cli info "${OBJECT_ID}" | grep -w "node\.name" | cut -d'"' -f2)
        if [ "${NODE_NAME}" = "xrdp-sink" ] || [ "${NODE_NAME}" = "xrdp-source" ]; then
            pw-cli destroy "${OBJECT_ID}"
        fi
    done
    [ "${1:-}" = "-d" ] && exit 0
    export PIPEWIRE_LOG_SYSTEMD=false
    if [ "${1:-}" = "-l" ]; then
        if [ -n "${2:-}" ]; then
            export PIPEWIRE_DEBUG="${2}"
        else
            export PIPEWIRE_DEBUG=3
        fi
        DISPLAY_NUM=$(printf '%s' "${DISPLAY:-:0}" | sed -e 's/^[^0-9]//' | cut -d. -f1)
        export PIPEWIRE_LOG="/tmp/xrdp_pipewire_${DISPLAY_NUM}.log"
    else
        export PIPEWIRE_DEBUG=1
    fi
    PWCLI=pw-cli
    PW_VERSION=$(pipewire --version | sed -e "s/[ a-zA-Z]//g" | tail -n 1)
    if [ "${PW_VERSION}" = "0.3.58" ]; then
        PWCLI="$(dirname "$0")/pw-cli_0358_mod"
    fi
    SINK_PROPS="node.name=xrdp-sink"
    SRC_PROPS="node.name=xrdp-source"
    "${PWCLI}" -m -d load-module libpipewire-module-xrdp \
        "sink.node.latency=${QUANTUMVAL}" \
        "sink.stream.props={${SINK_PROPS}}" \
        "source.stream.props={${SRC_PROPS}}" > /dev/null &

    sleep 1
    pw-metadata -n settings 0 clock.force-quantum "${QUANTUMVAL}" > /dev/null
    pw-metadata -n settings 0 default.clock.force-quantum "${QUANTUMVAL2}" > /dev/null
    pw-metadata -n settings 0 default.clock.quantum "${QUANTUMVAL2}" > /dev/null
    pw-metadata -n settings 0 default.clock.min-quantum "${QUANTUMVAL2}" > /dev/null
    pw-metadata -n settings 0 default.clock.rate 44100 > /dev/null
    if command -v pactl > /dev/null; then
        pactl set-default-sink xrdp-sink
        pactl set-default-source xrdp-source
    fi
fi
