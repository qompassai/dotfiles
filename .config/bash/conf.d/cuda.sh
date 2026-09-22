# #################################################################
# /qompassai/.config/bash/conf.d/cuda.sh
# Qompass AI Cuda
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Qompass AI
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# #################################################################
export CUDA_HOME=/opt/cuda
export CUDA_PATH=/opt/cuda
export CUDAToolkit_ROOT=/opt/cuda
export CUDACXX="$CUDA_HOME/bin/nvcc"
export CUDAHOSTCXX=/usr/bin/clang++
export TORCH_CUDA_ARCH_LIST="8.9+PTX"

export CMAKE_CUDA_COMPILER="$CUDACXX"
export CMAKE_CUDA_HOST_COMPILER="$CUDAHOSTCXX"
export CUDAARCHS=89
export CMAKE_CUDA_ARCHITECTURES=89

export CPATH="$CUDA_HOME/include${CPATH:+:$CPATH}"
export LIBRARY_PATH="$CUDA_HOME/lib64:$CUDA_HOME/lib${LIBRARY_PATH:+:$LIBRARY_PATH}"

case ":$PATH:" in
  *":$CUDA_HOME/bin:"*) ;;
  *) export PATH="$CUDA_HOME/bin:$PATH" ;;
esac

_cuda_lib="$CUDA_HOME/lib64:$CUDA_HOME/lib:$CUDA_HOME/targets/x86_64-linux/lib"
case ":${LD_LIBRARY_PATH:-}:" in
  *":$CUDA_HOME/targets/x86_64-linux/lib:"*) ;;
  *) export LD_LIBRARY_PATH="${_cuda_lib}${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" ;;
esac

export CUDNN_INCLUDE_DIR=/usr/include
export CUDNN_LIBRARY=/usr/lib/libcudnn.so

export CUDA_DEVICE_ORDER=PCI_BUS_ID
export CUDA_MODULE_LOADING=LAZY
export PYTORCH_ALLOC_CONF=expandable_segments:True
export BUILDCACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/buildcache"
export BUILDCACHE_MAX_CACHE_SIZE=50000000000   # bytes; 50G
export CMAKE_C_COMPILER_LAUNCHER=buildcache
export CMAKE_CXX_COMPILER_LAUNCHER=buildcache
export CMAKE_CUDA_COMPILER_LAUNCHER=buildcache
