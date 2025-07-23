#!/usr/bin/env bash
# /qompassai/Shell/.profile.d/02-cuda.sh
# # Copyright (C) 2025 Qompass AI, All rights reserved
# -----------------------------
export NVHPC="/opt/nvidia/hpc_sdk/Linux_x86_64/25.3"
export NVCOMPILERS="$NVHPC/compilers"
export NVMATH="$NVHPC/math_libs"
export OPTIX_INSTALL_DIR="/opt/optix-sdk"
export CUDAToolkit_ROOT="$NVHPC/cuda"
export CUDA_HOME="$CUDAToolkit_ROOT"
export CUDA_NVCC_EXECUTABLE="sccache $CUDAToolkit_ROOT/bin/nvcc"
export CUDA_PATH="$CUDAToolkit_ROOT"
export CUDA_VISIBLE_DEVICES="0,1,2"
export CC="$NVCOMPILERS/bin/nvc"
export CXX="$NVCOMPILERS/bin/nvc++"
export FC="$NVCOMPILERS/bin/nvfortran"
export CMAKE_CUDA_ARCHITECTURES="89"
export CUDAFLAGS="-arch=sm_89"
export LD_LIBRARY_PATH="$NVHPC/cuda/lib64:$NVCOMPILERS/lib:$NVMATH/lib64:$OPTIX_INSTALL_DIR/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export LIBRARY_PATH="$NVHPC/cuda/lib64:$NVCOMPILERS/lib:$NVMATH/lib64${LIBRARY_PATH:+:$LIBRARY_PATH}"
export NVCC_PREPEND_FLAGS="-Wno-error=attributes"
export NVHPC_CUDA_FLAGS="-Wno-error=attributes"
export PATH="$NVHPC/cuda/bin:$NVCOMPILERS/bin:$NVMATH/bin:$OPTIX_INSTALL_DIR/bin${PATH:+:$PATH}"
export LD_LIBRARY_PATH=$(echo "$LD_LIBRARY_PATH" | tr ':' '\n' | awk '!x[$0]++' | grep -v '^$' | paste -sd: -)
export LIBRARY_PATH=$(echo "$LIBRARY_PATH" | tr ':' '\n' | awk '!x[$0]++' | grep -v '^$' | paste -sd: -)
export PATH=$(echo "$PATH" | tr ':' '\n' | awk '!x[$0]++' | grep -v '^$' | paste -sd: -)
