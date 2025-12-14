#!/usr/bin/env sh
# /qompassai/Shell/.profile.d/30-hf.sh
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
export HF_TOKEN=$(pass show hf)
export HF_HOME="$HOME/.cache/huggingface"
export HF_HUB_CACHE="$HOME/.cache/huggingface/hub"
export HF_DATASETS_CACHE="$HOME/.cache/huggingface/datasets"
export HF_METRICS_CACHE="$HOME/.cache/huggingface/metrics"
export HF_MODULES_CACHE="$HOME/.cache/huggingface/modules"
export HF_HUB_ENABLE_HF_TRANSFER="1"
export HF_HUB_DISABLE_PROGRESS_BARS="0"
export HF_HUB_DISABLE_TELEMETRY="1"
export HF_HUB_OFFLINE="0"
export HF_ENDPOINT="https://huggingface.co"
export HF_API_ENDPOINT="https://huggingface.co/api"
hfcli() {
    export HF_TOKEN=$(pass show hf)
    hf "$@"
}
hfsearch() {
    if [ $# -eq 0 ]; then
        echo "Usage: hfsearch <search_term>"
        return 1
    fi
    HF_TOKEN=$(pass show hf) hf search "$@"
}
hfcache() {
    echo "=== Hugging Face Cache Usage ==="
    du -sh "$HF_HOME" 2>/dev/null || echo "Cache directory not found"
    echo ""
    echo "=== Detailed Cache Breakdown ==="
    HF_TOKEN=$(pass show hf) hf scan-cache
}
hfget() {
    if [ $# -lt 1 ]; then
        echo "Usage: hfget <model_name> [revision]"
        echo "Example: hfget microsoft/DialoGPT-medium"
        return 1
    fi
    local model="$1"
    local revision="${2:-main}"
    echo "Downloading $model (revision: $revision)..."
    HF_TOKEN=$(pass show hf) hf download "$model" --revision "$revision" --resume-download
}
export -f hfcli hfsearch hfcache hfget
