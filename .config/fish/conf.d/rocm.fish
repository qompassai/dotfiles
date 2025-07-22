# ROCm/AMD GPU
set -x ROCM_PATH /opt/rocm

if test -d /opt/rocm/bin
    fish_add_path -P /opt/rocm/bin
end

if test -d /opt/rocm/lib
    fish_add_path -P /opt/rocm/lib
end

if test -d /opt/rocm/rocgdb/bin
    fish_add_path -P /opt/rocm/rocgdb/bin
end

