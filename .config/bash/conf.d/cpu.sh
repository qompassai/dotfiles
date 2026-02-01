#!/usr/bin/env bash

# /qompassai/dotfiles/.config/bash/conf.d/cpu.sh
# Qompass AI Bash CPU Script
# Copyright (C) 2026 Qompass AI, All rights reserved
# ----------------------------------------
export CPUINFER_CPU_INSTRUCT=AVX512
export CPUINFER_ENABLE_AMX=ON
export CPUINFER_ENABLE_AVX512_VNNI=ON
export CPUINFER_ENABLE_AVX512_BF16=ON
export CPUINFER_ENABLE_AVX512_VBMI=ON
export KFR_ARCH=avx2
