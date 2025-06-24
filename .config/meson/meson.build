# ~/.config/meson/meson.build
# ---------------------------
# Copyright (C) 2025 Qompass AI, All rights reserved

cmake = import('cmake')

cmake_opts = cmake.subproject_options()
cmake_opts.add_cmake_defines({
  'CMAKE_POLICY_DEFAULT_CMP0116': 'NEW',
  'CMAKE_POLICY_DEFAULT_CMP0113': 'NEW',
})

if get_option('enable_llvm')
  llvm_dep = cmake.subproject('llvm', options: cmake_opts)
endif
