# /qompassai/dotfiles/.config/fish/config.fish
# Qompass AI Fish Config
# Copyright (C) 2025 Qompass AI, All rights reserved
#---------------------------------------------------

if command -q zoxide
    zoxide init fish | source
end

if status is-interactive
    set fish_greeting ""
end

set -x NVHPC_ROOT /opt/nvidia/hpc_sdk/Linux_x86_64/25.3
set -x NVHPC_VERSION 25.3
set -x NVHPC_COMPILERS $NVHPC_ROOT/compilers
set -x NVHPC_COMM_LIBS $NVHPC_ROOT/comm_libs
set -x NVHPC_MATH_LIBS $NVHPC_ROOT/math_libs

set -x CUDA_PATH $NVHPC_ROOT/cuda
set -x CUDA_ROOT $NVHPC_ROOT/cuda
set -x CUDA_HOME $NVHPC_ROOT/cuda
set -x CUDA_VERSION 12.8
set -x CMAKE_CUDA_ARCHITECTURES 89
set -x CUDAFLAGS "-arch=sm_89"
set -x CFLAGS "-fno-builtin-isnan -fno-builtin-isnanf -fno-builtin-isnanl $CFLAGS"
set -x CXXFLAGS "-fno-builtin-isnan -fno-builtin-isnanf -fno-builtin-isnanl $CXXFLAGS"
set -x NVCC_PREPEND_FLAGS "-fno-builtin-isnan -fno-builtin-isnanf -fno-builtin-isnanl"
set -x CFLAGS "-fno-math-errno $CFLAGS"
set -x CXXFLAGS "-fno-math-errno $CXXFLAGS"
set -x FORCE_COLOR 1
set -x LANG en_US.UTF-8
set -x LC_ALL en_US.UTF-8
set -x CC "$NVHPC_COMPILERS/bin/nvc -Wno-error=attributes"
set -x CXX "$NVHPC_COMPILERS/bin/nvc++ -Wno-error=attributes"
set -x FC "$NVHPC_COMPILERS/bin/nvfortran"
set -x TERM xterm-256color
set -x SSH_AUTH_SOCK (gpgconf --list-dirs agent-ssh-socket)
set -e SSH_AGENT_PID
set -x NPM_PACKAGES "$HOME/.npm-packages"
set -x MANPATH "$NPM_PACKAGES/share/man" $MANPATH
fish_add_path -p $NPM_PACKAGES/bin
fish_add_path -p $NVHPC_ROOT/compilers/bin
fish_add_path -p $NVHPC_ROOT/cuda/bin
fish_add_path -p $NVHPC_ROOT/comm_libs/mpi/bin

set -x LD_LIBRARY_PATH \
    $NVHPC_ROOT/cuda/lib64 \
    $NVHPC_ROOT/compilers/lib \
    $NVHPC_ROOT/math_libs/lib64 \
    $NVHPC_ROOT/comm_libs/mpi/lib \
    $LD_LIBRARY_PATH

fish_add_path -p /opt/rocm/bin /opt/rocm/lib
fish_add_path -p /usr/lib/jvm/default/bin
fish_add_path -p ~/.cargo/bin
fish_add_path -p /usr/bin/site_perl /usr/bin/vendor_perl /usr/bin/core_perl

set -x MANPATH $NVHPC_ROOT/compilers/man $MANPATH
set -x CPATH $NVHPC_ROOT/cuda/include $NVHPC_ROOT/compilers/include $CPATH

set -x ROCM_PATH /opt/rocm
