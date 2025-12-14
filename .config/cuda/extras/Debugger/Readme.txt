--------------------------------------------------------------------------------

                                 DEBUGGER API

--------------------------------------------------------------------------------

The debugger API is a set of routines that allows debuggers to control the
execution and to inspect NVIDIA GPUs running CUDA kernels. Third-party 
debuggers must be linked against the CUDA driver library (libcuda.so) to use
the debugger API.

The files in the extras/debugger directory contains all the files related to
the debugger API:

 cudadebugger.h

     The header file for the debugger API.
 
 cuda-stdint.h 

     Support file for cudadebugger.h. Includes basic types used by
     cudadebugger.h.

See the CUDA Toolkit documentation for more details about the debugger API.
