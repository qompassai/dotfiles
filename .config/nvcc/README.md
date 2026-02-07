NVCC Compiler Flags

Official Documentation: https://docs.nvidia.com/cuda/cuda-compiler-driver-nvcc/

File and Path Specifications

--allow-unsupported-compiler (-allow-unsupported-compiler)
  Disable nvcc check for supported host compiler versions

--archiver-binary executable (-arbin)
  Specify the path of the archiver tool

--compiler-bindir directory (-ccbin)
  Specify directory with host compiler executable

--cudadevrt {none|static} (-cudadevrt)
  Specify CUDA device runtime library type

--define-macro def,... (-D)
  Define macros for preprocessing

--dependency-output file (-MF)
  Specify dependency output file

--generate-dependency-targets (-MP)
  Add empty target for each dependency

--include-path path,... (-I)
  Specify include search paths

--libdevice-directory directory (-ldir)
  Specify libdevice library files directory

--library library,... (-l)
  Specify libraries for linking

--library-path path,... (-L)
  Specify library search paths

--objdir-as-tempdir (-objtemp)
  Create intermediate files in object directory

--output-directory directory (-odir)
  Specify output file directory

--output-file file (-o)
  Specify output file name and location

--pre-include file,... (-include)
  Pre-include header files during preprocessing

--system-include path,... (-isystem)
  Specify system include search paths

--target-directory string (-target-dir)
  Specify subfolder in targets directory

--undefine-macro def,... (-U)
  Undefine existing macro

Compilation Phase Options

--compile (-c)
  Compile to object file

--cubin (-cubin)
  Compile to device-only .cubin files

--cuda (-cuda)
  Compile .cu to .cu.cpp.ii file

--device-c (-dc)
  Compile to relocatable device code object

--device-link (-dlink)
  Link relocatable device code

--device-w (-dw)
  Compile to executable device code object

--fatbin (-fatbin)
  Compile to device-only .fatbin files

--generate-dependencies (-M)
  Generate dependency file for Makefile

--generate-dependencies-with-compile (-MD)
  Generate dependencies and compile

--generate-nonsystem-dependencies (-MM)
  Generate dependencies excluding system headers

--generate-nonsystem-dependencies-with-compile (-MMD)
  Same as -MD but skip system headers

--lib (-lib)
  Create library archive

--link (-link)
  Compile and link all input files (default)

--ltoir (-ltoir)
  Compile to LTO IR output

--optix-ir (-optix-ir)
  Compile to OptiX IR output

--preprocess (-E)
  Preprocess input files

--ptx (-ptx)
  Compile to device-only .ptx files

--run (-run)
  Compile, link, and execute

Compiler/Linker Behavior Options

--augment-host-linker-script (-aug-hls)
  Generate augmented host linker script

--compress-mode {default|size|speed|balance|none} (-compress-mode)
  Choose device code compression

--debug (-g)
  Generate debug information for host code

--device-debug (-G)
  Generate debug information for device code

--dlink-time-opt (-dlto)
  Perform link-time optimization

--dopt kind (-dopt)
  Enable device code optimization

--expt-extended-lambda (-expt-extended-lambda)
  Alias for --extended-lambda

--expt-relaxed-constexpr (-expt-relaxed-constexpr)
  Allow __device__ constexpr functions in host code

--extended-lambda (-extended-lambda)
  Allow __host__, __device__ in lambda declarations

--extensible-whole-program (-ewp)
  Generate extensible whole program device code

--forward-unknown-to-host-compiler
  Forward unknown options to host compiler

--frandom-seed (-frandom-seed)
  Use specified random seed for deterministic output

--ftemplate-backtrace-limit limit (-ftemplate-backtrace-limit)
  Set template instantiation backtrace limit

--ftemplate-depth limit (-ftemplate-depth)
  Set max instantiation depth for template classes

--gen-opt-lto (-gen-opt-lto)
  Run optimizer before generating LTO IR

--generate-line-info (-lineinfo)
  Generate line-number information for device code

--host-linker-script {use-lcs|gen-lcs} (-hls)
  Use/generate host linker script

--jobserver (-jobserver)
  Use GNU Make jobserver with split compilation

--machine {64} (-m)
  Specify 64-bit architecture

--m64 (-m64)
  Alias for --machine=64

--no-compress (-no-compress)
  Don't compress device code in fatbinary

--no-exceptions (-noeh)
  Disable exception handling for host code

--no-host-device-initializer-list (-nohdinitlist)
  Don't treat std::initializer_list as __host__ __device__

--Ofast-compile level (-Ofc)
  Specify fast-compile level for device code

--optimization-info kind,... (-opt-info)
  Provide optimization reports

--optimize level (-O)
  Specify optimization level for host code

--profile (-pg)
  Instrument code for gprof

--relocatable-link (-r)
  Generate relocatable object when linking

--relocatable-ptx (-reloc-ptx)
  Insert PTX from relocatable fatbins

--split-compile number (-split-compile)
  Perform optimizations in parallel

--split-compile-extended number (-split-compile-extended)
  Aggressive parallel compilation

--static-global-template-stub {true|false} (-static-global-template-stub)
  Force static linkage for global template stubs

--std {c++03|c++11|c++14|c++17|c++20} (-std)
  Select C++ dialect

--x {c|c++|cu} (-x)
  Explicitly specify input language

Phase-Specific Options

--archive-options options,... (-Xarchive)
  Pass options to library manager

--compiler-options options,... (-Xcompiler)
  Pass options to compiler/preprocessor

--linker-options options,... (-Xlinker)
  Pass options to host linker

--nvlink-options options,... (-Xnvlink)
  Pass options to nvlink

--ptxas-options options,... (-Xptxas)
  Pass options to ptxas

GPU Architecture Options

See: https://docs.nvidia.com/cuda/cuda-programming-guide/02-basics/nvcc.html

--gpu-architecture arch (-arch)
  Specify virtual GPU architecture

--gpu-code code,... (-code)
  Specify GPU code generation

--generate-code specification,... (-gencode)
  Specify architecture and code

Additional Flags

--help (-h)
  Display help information

--list-gpu-arch
  List supported virtual GPU architectures

--list-gpu-code
  List supported real GPU architectures

--verbose (-v)
  Switch to verbose mode

--version (-V)
  Display compiler version

For the complete and most up-to-date list, consult:
https://docs.nvidia.com/cuda/cuda-compiler-driver-nvcc/

