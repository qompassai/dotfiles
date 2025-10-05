# cmake.fish
# Qompass AI Cmake Fish Config
# Copyright (C) 2025 Qompass AI, All rights reserved
# ----------------------------------------
function cmake
    command cmake -DCMAKE_POLICY_VERSION_MINIMUM=4.1 $argv
end

