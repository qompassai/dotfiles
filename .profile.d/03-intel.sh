#!/usr/bin/env sh
# /qompassai/Shell/.profile.d/03-intel.sh
# -----------------------------
# Copyright (C) 2025 Qompass AI, All rights reserved

export SYCL_DEVICE_FILTER=level_zero:gpu,opencl:gpu
#source /opt/intel/oneapi/setvars.sh > /dev/null 2>&1 || true
#export TBB_ROOT_DIR=/usr
#export TBB_LIBRARIES=/usr/lib/libtbb.so.2020
export ONEDNN_VERBOSE=all
alias use_intel_gpu="export ZE_AFFINITY_MASK=0.0"
alias use_nvidia_gpu="export ZE_AFFINITY_MASK=1.0"
