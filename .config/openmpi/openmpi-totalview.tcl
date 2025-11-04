# /qompassai/dotfiles/.config/openmpi/openmpi-totalview.tcl
# Qompass AI OpenMPI TotalView Config
# Copyright (C) 2025 Qompass AI, All rights reserved
#################################################
$HEADER$
proc mpi_auto_run_starter {loaded_id} {
    set starter_programs {mpirun mpiexec orterun}
    set executable_name [TV::symbol get $loaded_id full_pathname]
    set file_component [file tail $executable_name]

    if {[lsearch -exact $starter_programs $file_component] != -1} {
        puts "**************************************"
        puts "Automatically starting $file_component"
        puts "**************************************"
        dgo
    }
}
dlappend TV::image_load_callbacks mpi_auto_run_starter
