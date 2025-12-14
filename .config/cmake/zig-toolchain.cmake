# cmake/zig-toolchain.cmake
# Zig Toolchain for CMake with musl/glibc and optimization mode toggles
# Copyright (C) 2025 Qompass AI

# -------------------- User-configurable variables -----------------------

set(ZIG_OPTIMIZE_LEVEL "safe" CACHE STRING "Zig optimization level")

set(ZIG_LIBC "glibc" CACHE STRING "C library to target (glibc or musl)")

set(ZIG_CPU "x86_64" CACHE STRING "Target CPU")

set(ZIG_TARGET_TRIPLE "${ZIG_CPU}-linux-${ZIG_LIBC}" CACHE STRING "Zig target triple")

# -------------------- Compiler / linker setup --------------------------

set(CMAKE_C_COMPILER "zig")
set(CMAKE_C_COMPILER_ARG1 "cc")
set(CMAKE_CXX_COMPILER "zig")
set(CMAKE_CXX_COMPILER_ARG1 "c++")
set(CMAKE_AR "zig")
set(CMAKE_RANLIB "zig")
set(CMAKE_STRIP "zig")

# -------------------- Compiler flags -----------------------------------

set(CMAKE_C_FLAGS_INIT "-target ${ZIG_TARGET_TRIPLE} -Doptimize=${ZIG_OPTIMIZE_LEVEL}")
set(CMAKE_CXX_FLAGS_INIT "-target ${ZIG_TARGET_TRIPLE} -Doptimize=${ZIG_OPTIMIZE_LEVEL}")

# -------------------- Cross-compilation system info --------------------

set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR ${ZIG_CPU})
set(CMAKE_SYSROOT "")

set(CMAKE_POSITION_INDEPENDENT_CODE ON)
