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
export CUDAHOSTCXX=/usr/bin/g++
case ":$PATH:" in
  *":$CUDA_HOME/bin:"*) ;;
  *) export PATH="$CUDA_HOME/bin:$PATH" ;;
esac
case ":${LD_LIBRARY_PATH:-}:" in
  *":$CUDA_HOME/lib64:"*) ;;
  *)
    export LD_LIBRARY_PATH="$CUDA_HOME/lib64${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
    ;;
esac
