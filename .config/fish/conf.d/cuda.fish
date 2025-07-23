# CUDA & NVIDIA HPC SDK
#set -x NVHPC_ROOT /opt/nvidia/hpc_sdk/Linux_x86_64/25.3
#set -x NVHPC_VERSION 25.3
#set -x NVHPC_COMPILERS $NVHPC_ROOT/compilers
#set -x NVHPC_COMM_LIBS $NVHPC_ROOT/comm_libs
#set -x NVHPC_MATH_LIBS $NVHPC_ROOT/math_libs

#set -x CUDA_PATH $NVHPC_ROOT/cuda
#set -x CUDA_ROOT $NVHPC_ROOT/cuda
#set -x CUDA_HOME $NVHPC_ROOT/cuda
#set -x CUDA_VERSION 12.8
#set -x CMAKE_CUDA_ARCHITECTURES 89
#set -x CUDAFLAGS "-arch=sm_89"

#set -x CFLAGS "-fno-builtin-isnan -fno-builtin-isnanf -fno-builtin-isnanl -fno-math-errno $CFLAGS"
#set -x CXXFLAGS "-fno-builtin-isnan -fno-builtin-isnanf -fno-builtin-isnanl -fno-math-errno $CXXFLAGS"
#set -x NVCC_PREPEND_FLAGS "-fno-builtin-isnan -fno-builtin-isnanf -fno-builtin-isnanl"

#set -x CC "$NVHPC_COMPILERS/bin/nvc -Wno-error=attributes"
#set -x CXX "$NVHPC_COMPILERS/bin/nvc++ -Wno-error=attributes"
#set -x FC "$NVHPC_COMPILERS/bin/nvfortran"

#fish_add_path -P $NVHPC_ROOT/compilers/bin
#fish_add_path -P $NVHPC_ROOT/cuda/bin
#fish_add_path -P $NVHPC_ROOT/comm_libs/mpi/bin

#set -x LD_LIBRARY_PATH \
#    $NVHPC_ROOT/cuda/lib64 \
#    $NVHPC_ROOT/compilers/lib \
#    $NVHPC_ROOT/math_libs/lib64 \
#    $NVHPC_ROOT/comm_libs/mpi/lib \
#    $LD_LIBRARY_PATH

#set -x MANPATH $NVHPC_ROOT/compilers/man $MANPATH
#set -x CPATH $NVHPC_ROOT/cuda/include $NVHPC_ROOT/compilers/include $CPATH

function gpu_stats
    nvidia-smi --query-gpu=timestamp,name,utilization.gpu,utilization.memory --format=csv
end

