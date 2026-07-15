<!-- #################################################################
<!-- /qompassai/.config/buildcache/README.md
<!-- Qompass AI README
<!-- SPDX-License-Identifier: Apache-2.0
<!-- Copyright (c) 2026 Qompass AI
<!--
<!-- Licensed under the Apache License, Version 2.0 (the "License");
<!-- you may not use this file except in compliance with the License.
<!-- You may obtain a copy of the License at:
<!--   http://www.apache.org/licenses/LICENSE-2.0
<!--
<!-- Unless required by applicable law or agreed to in writing, software
<!-- distributed under the License is distributed on an "AS IS" BASIS,
<!-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
<!-- See the License for the specific language governing permissions and
<!-- limitations under the License.
<!-- #################################################################-->

# Benchmarks

## LLVM Compilation

For this benchmark, LLVM *(2021-01-17, Git commit: cfec6cd50c36f3db2fcd4084a8ef4df834a4eb24)* was built from source as follows:

```sh
mkdir build && cd build
cmake -DCMAKE_C_COMPILER_LAUNCHER=buildcache -DCMAKE_CXX_COMPILER_LAUNCHER=buildcache -G Ninja -DCMAKE_BUILD_TYPE=Release ../llvm
time ninja
```

The system used for the benchmark was:

* **CPU**: AMD Ryzen 7 1800x (8-core x86-64, underclocked to 3.0 GHz).
* **Disk**: 1TB NVMe (960 EVO)
* **RAM**: 32GiB DDR4 @ 3000 MHz
* **OS**: Linux (Ubuntu 20.04)
* **Compiler**: GCC 9.3.0
* **BuildCache**: 0.24.0

### TL;DR graph

![LLVM build time speedup](llvm-benchmark-graph.jpg)

### No cache

| Time | Speed |
|---|---|
| 19m50.9s | 1.0x |

### Local cache, preprocessor mode, no compression

|  | Time | Speed |
|---|---|---|
| Cold cache | 20m55.7s | 0.95x |
| Warm cache | 1m38.7s | 12.1x |

Cache size: **240.8 MiB**

### Local cache, direct mode, no compression

|  | Time | Speed |
|---|---|---|
| Cold cache | 20m56.2s | 0.95x |
| Warm cache | 0m32.0s | 37.2x |

Cache size: **326.7 MiB**

### Local cache, direct mode, LZ4 compression

|  | Time | Speed |
|---|---|---|
| Cold cache | 20m59.0s | 0.95x |
| Warm cache | 0m31.8s | 37.4x |

Cache size: **134.6 MiB**

### Local cache, direct mode, ZSTD compression

|  | Time | Speed |
|---|---|---|
| Cold cache | 20m56.7s | 0.95x |
| Warm cache | 0m31.9s | 37.3x |

Cache size: **86.9 MiB**

### Ccache

For reference, the same compilation was performed with Ccache version 3.7.7 (using the default configuration) on the same system, with the following results:

|  | Time | Speed |
|---|---|---|
| Cold cache | 20m55.7s | 0.95x |
| Warm cache | 0m36.0s | 33.1x |

Cache size: **354.8 MiB**


# Configuration

BuildCache can be configured via environment variables and a per-cache JSON
configuration file. The optional configuration file is located in the cache
root directory, and is called `config.json` (e.g.
`$HOME/.buildcache/config.json`).

The following options control the behavior of BuildCache:

| Env | JSON | Description | Default |
| --- | --- | --- | --- |
| `BUILDCACHE_ACCURACY` | `accuracy` | Caching accuracy (see below) | DEFAULT |
| `BUILDCACHE_CACHE_LINK_COMMANDS` | `cache_link_commands` | Enable caching of link commands | false |
| `BUILDCACHE_CACHE_ON_FAILURE` | `cache_on_failure` | Cache commands even if they exit with a failure status (non-zero exit code) | false |
| `BUILDCACHE_COMPRESS` | `compress` | Allow the use of compression when caching (overrides hard links) | true |
| `BUILDCACHE_COMPRESS_FORMAT` | `compress_format` | Cache compresion format (see below) | DEFAULT |
| `BUILDCACHE_COMPRESS_LEVEL` | `compress_level` | Cache compresion level (see below) | -1 |
| `BUILDCACHE_DEBUG` | `debug` | Debug level | None |
| `BUILDCACHE_DIR` | - | The cache root directory | `$HOME/.buildcache` |
| `BUILDCACHE_DIRECT_MODE` | `direct_mode` | Enable direct mode | true |
| `BUILDCACHE_DISABLE` | `disable` | Disable caching (bypass BuildCache) | false |
| `BUILDCACHE_HARD_LINKS` | `hard_links` | Allow the use of hard links when caching | false |
| `BUILDCACHE_HASH_EXTRA_FILES` | `hash_extra_files` | Extra file(s) whose content to add to the hash | None |
| `BUILDCACHE_IMPERSONATE` | `impersonate` | Explicitly set the executable to wrap | None |
| `BUILDCACHE_LOG_FILE` | `log_file` | Log file path (empty for stdout) | None |
| `BUILDCACHE_LUA_PATH` | `lua_paths` | Extra path(s) to Lua wrappers | None |
| `BUILDCACHE_MAX_CACHE_SIZE` | `max_cache_size` | Cache size limit in bytes | 5368709120 |
| `BUILDCACHE_MAX_LOCAL_ENTRY_SIZE` | `max_local_entry_size` | Local cache entry size limit in bytes (uncompressed) | 134217728 |
| `BUILDCACHE_MAX_REMOTE_ENTRY_SIZE` | `max_remote_entry_size` | Remote cache entry size limit in bytes (uncompressed) | 134217728 |
| `BUILDCACHE_PERF` | `perf` | Enable performance logging | false |
| `BUILDCACHE_PREFIX` | `prefix` | Prefix command for cache misses | None |
| `BUILDCACHE_READ_ONLY` | `read_only` | Only read and use the cache without updating it | false |
| `BUILDCACHE_READ_ONLY_REMOTE` | `read_only_remote` | Only read and use the remote cache without updating it (implied by `BUILDCACHE_READ_ONLY`) | false |
| `BUILDCACHE_REDIS_USERNAME` | `redis_username` | Redis auth username | None |
| `BUILDCACHE_REDIS_PASSWORD` | `redis_password` | Redis auth password (username optional) | None |
| `BUILDCACHE_REMOTE` | `remote` | Address of remote cache server (`protocol://host:port/path`, where `protocol` can be `http`, `redis` or `s3`, and `port` and `path` are optional) | None |
| `BUILDCACHE_REMOTE_LOCKS` | `remote_locks` | Use a (potentially slower) file locking mechanism that is safe if the local cache is on a fileshare | false |
| `BUILDCACHE_S3_ACCESS` | `s3_access` | S3 access key (will fallback to AWS_ACCESS_KEY_ID) | None |
| `BUILDCACHE_S3_SECRET` | `s3_secret` | S3 secret key (will fallback to AWS_SECRET_ACCESS_KEY) | None |
| `BUILDCACHE_S3_SIGNATURE_VERSION` | `s3_signature_version` | Use S3 signature version v2 (2) or v4 (4) | 4 |
| `BUILDCACHE_STAT_ID` | `stat_id` | Stat ID for per-session statistics partitioning | None |
| `BUILDCACHE_TERMINATE_ON_MISS` | `terminate_on_miss` | Stop building if not found entry in a cache | false |

Note: Currently, only the TI C6x back end supports the `cache_link_commands`
option.

An example configuration file:

```json
{
  "max_cache_size": 10000000000,
  "prefix": "icecc",
  "remote": "redis://my-server:6379",
  "debug": 3,
  "lua_paths": [
    "/home/myname/buildcache-lua",
    "/opt/buildcache-lua"
  ],
  "compress_format": "ZSTD"
}
```

To see the configuration options that are in effect, run:

```bash
$ buildcache --show-config
```

## Debugging

To get debug output from a BuildCache run, set the environment variable
`BUILDCACHE_DEBUG` to the desired debug level (debug output is disabled by
default):

| BUILDCACHE_DEBUG | Level   | Comment              |
| ---------------- | ------- | -------------------- |
| 1                | DEBUG   | Maximum printouts    |
| 2                | INFO    |                      |
| 3                | WARNING |                      |
| 4                | ERROR   |                      |
| 5                | FATAL   |                      |
| -1               | -       | Disable debug output |

For instance:

```bash
$ BUILDCACHE_DEBUG=2 buildcache g++ -c -O2 hello.cpp -o hello.o
```

It is also possible to redirect the log output to a file using the
`BUILDCACHE_LOG_FILE` setting.

## Direct mode

In direct mode BuildCache will try to find a cache hit based on the hash of
the input file and its indirect input files (e.g. C/C++ include files),
without running the preprocessor step. This can be significantly faster than
the standard method of running the preprocessor to get a hash.

The direct mode is enabled when `BUILDCACHE_DIRECT_MODE` is set to true.

## Caching accuracy

With the caching accuracy setting, `BUILDCACHE_ACCURACY`, it is possible to
control how strict BuildCache is when checking for cache hits. This gives an
opportunity to trade correctness for performance.

| BUILDCACHE_ACCURACY | Comment                                       |
| ------------------- | --------------------------------------------- |
| STRICT              | Maximum correctness                           |
| DEFAULT             | A balance between performance and correctness |
| SLOPPY              | Optimize for maximum cache hit ratio          |

The default accuracy mode is `DEFAULT`.

### STRICT

In `STRICT` accuracy mode, the cache lookup will consider absolute file paths
and line numbers whenever debugging symbols or coverage info is generated. This
means that when your build includes debugging symbols or coverage info, you will
get a cache miss if the absolute file path or any line number has changed.

This mode is suitable if you intend to use the final executable for running code
coverage tests or for debugging. The downside is that you may often get cache
misses, especially in a shared centralized cache that contains objects from
different machines with different build paths.

### DEFAULT

The `DEFAULT` mode is similar to the `STRICT` mode, except that it will ignore
file path and line number information for debug builds.

Note that in many situations it is still possible to use the generated
executables for debugging. For instance, with GDB you can
[specify a custom source code path](https://sourceware.org/gdb/current/onlinedocs/gdb/Source-Path.html)
during a debugging session.

Binaries built with this mode can be used for code coverage generation.

### SLOPPY

With the `SLOPPY` mode, absolute file paths and line number information are
always ignored during cache lookup, which improves cache hit ratio. The downside
is that you may not be able to use the binaries for code coverage.

## Cache compression format

With the cache compression format setting, `BUILDCACHE_COMPRESS_FORMAT`, it is
possible to control how the generated caches are compressed.

| BUILDCACHE_COMPRESS_FORMAT   | Comment                                                            |
| ---------------------------- | ------------------------------------------------------------------ |
| LZ4                          | Utilize LZ4 compression (faster compression, larger cache sizes)   |
| ZSTD                         | Utilize ZSTD compression (slower compression, smaller cache sizes) |
| DEFAULT                      | Utilize LZ4 compresson                                             |

The default compression format is `DEFAULT`.

Note: The "compress" setting must be set to true in order to utilize this
setting.

## Cache compression level

With the cache compression level setting, `BUILDCACHE_COMPRESS_LEVEL`, it is
possible to control the effort exerted by the compressor in order to produce
smaller cache files. See the documentation of your chosen compressor for more
information.

The default compression level is -1, which will utilize the default compression
level for the compressor.

Note: The "compress" setting must be set to true in order to utilize this
setting.

## BUILDCACHE_HASH_EXTRA_FILES

When calculating the hash of a translation unit, buildcache tries to take all
factors affecting the output into account. This includes things like the command line
or the preprocessed source. But sometimes there are additional factors
buildcache does not know about.

For example the Clang compiler has an option to read an exclusion list for
the sanitizers (`-fsanitize-blacklist`). This file affects the compilation
output but buildcache is not aware of that. By passing the file
name in the `BUILDCACHE_HASH_EXTRA_FILES` configuration option, its content
will be added to the translation unit hash and taken into account when
doing a cache lookup.

Another use case is the versioning of the cache content. Using the above example,
you may have tainted your cache as you forgot about the sanitizer
exclusion list in your first run. One solution would now be to drop the whole cache.
But in case of a shared remote cache, this might affect other caching tools and you
might not even be able to zap the remote cache. Creating a text file with a simple
versioning number and adding that to the `BUILDCACHE_HASH_EXTRA_FILES` will then
effectively abandon the previous cache output.

## BUILDCACHE_STAT_ID

Set `BUILDCACHE_STAT_ID` to a non-empty string to attribute cache lookups to a
named stat ID. Statistics are accumulated separately for each distinct stat ID,
making it easy to compare hit rates across different build configurations or
CI jobs that share the same cache directory.

```bash
export BUILDCACHE_STAT_ID=my-feature-branch
buildcache g++ -c foo.cpp -o foo.o
```

See `--show-stats` and `--zero-stats` in [usage](usage.md) for how to filter
the statistics output by session ID or wrapper name.

## S3 Authentication

BuildCache supports AWS S3 authentication with both v2 and v4 signature methods:

### Signature Version 4 (Default - Recommended)

AWS Signature Version 4 is the modern, secure authentication method and is used by default.

#### Configuration:
The AWS region is automatically detected from the S3 endpoint URL specified in `BUILDCACHE_REMOTE`:

```bash
# Examples of region auto-detection:
export BUILDCACHE_REMOTE="s3://my-bucket.s3.eu-west-1.amazonaws.com"      # → eu-west-1
export BUILDCACHE_REMOTE="s3://s3.us-west-2.amazonaws.com/my-bucket"      # → us-west-2
export BUILDCACHE_REMOTE="s3://s3-ap-southeast-1.amazonaws.com/bucket"    # → ap-southeast-1
export BUILDCACHE_REMOTE="s3://my-bucket.s3.amazonaws.com"                # → us-east-1 (default)
export BUILDCACHE_REMOTE="s3://localhost:9000/bucket"                     # → us-east-1 (non-AWS)
```

### Signature Version 2 (Legacy)

For compatibility with older S3-compatible services or specific requirements, you can enable v2 signatures:

```bash
export BUILDCACHE_S3_SIGNATURE_VERSION=2
```

### Credentials

BuildCache supports both specific and standard AWS credential formats:

#### Option 1: BuildCache-specific credentials
```bash
export BUILDCACHE_S3_ACCESS="your_access_key"
export BUILDCACHE_S3_SECRET="your_secret_key"
```

#### Option 2: Standard AWS credentials (automatic fallback)
```bash
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
```

If both are set, BuildCache-specific credentials take priority.

### Complete Example

```bash
# Modern setup with v4 signature (recommended)
export AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
export BUILDCACHE_REMOTE="s3://my-build-cache.s3.eu-central-1.amazonaws.com"

# Legacy setup with v2 signature
export BUILDCACHE_S3_ACCESS="AKIAIOSFODNN7EXAMPLE"
export BUILDCACHE_S3_SECRET="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
export BUILDCACHE_S3_SIGNATURE_VERSION=2
export BUILDCACHE_REMOTE="s3://my-build-cache.s3.amazonaws.com"
```

# Using BuildCache

To use BuildCache for your builds, simply prefix the build command with
`buildcache`. For instance:

```bash
$ buildcache g++ -c -O2 hello.cpp -o hello.o
```

## Using with CMake

A convenient solution for bigger CMake-based projects is to use the
`CMAKE_<LANG>_COMPILER_LAUNCHER` property to use BuildCache for all compilation commands,
like so:

```cmake
find_program(buildcache_program buildcache)
if(buildcache_program)
  set(CMAKE_C_COMPILER_LAUNCHER "${buildcache_program}")
  set(CMAKE_CXX_COMPILER_LAUNCHER "${buildcache_program}")

  # If building with MSVC, set the debug information format to Embedded.
  set(CMAKE_MSVC_DEBUG_INFORMATION_FORMAT "$<$<CONFIG:Debug,RelWithDebInfo>:Embedded>")
endif()
```

For find_program() to work here, it is neccessary that buildcache is available
on the PATH or that its path is specified in any of the environment variables
`CMAKE_PREFIX_PATH` or `CMAKE_PROGRAM_PATH` or any of the other search options
for [find_program](https://cmake.org/cmake/help/latest/command/find_program.html).

The compiler launchers can also be set when configuring CMake as follows:

```bash
cmake -DCMAKE_C_COMPILER_LAUNCHER=/path/to/buildcache    \
      -DCMAKE_CXX_COMPILER_LAUNCHER=/path/to/buildcache  \
      ...                                                \
      path/to/source/directory
```

## Symbolic links

Another alternative is to create symbolic links that redirect invokations of
your favourite compiler to go via BuildCache instead. For instance, if
`$HOME/bin` is early in your PATH, you can do the following:

```bash
$ ln -s /path/to/buildcache $HOME/bin/cc
$ ln -s /path/to/buildcache $HOME/bin/c++
$ ln -s /path/to/buildcache $HOME/bin/gcc
$ ln -s /path/to/buildcache $HOME/bin/g++
…
```

You can check that it works by invoking the compiler with BuildCache debugging
enabled:

```bash
$ BUILDCACHE_DEBUG=1 gcc
BuildCache[52286] (DEBUG) Invoked as symlink: gcc
…
```

## Impersonating a wrapped tool

Setting `BUILDCACHE_IMPERSONATE` forces BuildCache to operate as a tool wrapper,
using the value of the property as the tool to wrap. This allows pointing build
systems directly at the BuildCache executable instead of using symbolic links.
Note that when this setting has a non-default value BuildCache command line
arguments cannot be used - since any arguments are always forwarded to the
wrapped tool.

For example:

```bash
# Wraps execution of "g++ -c -O2 hello.cpp -o hello.o"
$ BUILDCACHE_IMPERSONATE=g++ buildcache -c -O2 hello.cpp -o hello.o

# Wraps execution of "g++ -s", probably not desired!
$ export BUILDCACHE_IMPERSONATE=g++
$ buildcache -s
```

## Using with icecream

[icecream](https://github.com/icecc/icecream) (or ICECC) is a tool for
distributed compilation. To use icecream you can set the environment variable
`BUILDCACHE_PREFIX` to the icecc executable, e.g:

```bash
$ BUILDCACHE_PREFIX=/usr/bin/icecc buildcache g++ -c -O2 hello.cpp -o hello.o
```

## Using a shared remote cache

To improve the cache hit ratio in a cluster of machines that often perform
the same or similar build tasks, you can use a shared remote cache (in
addition to the local cache).

To do so, set `BUILDCACHE_REMOTE` to a valid remote server address (see below).

### Redis

[Redis](https://redis.io/) is a fast, in-memory data store with built in
[LRU](https://en.wikipedia.org/wiki/Cache_replacement_policies#Least_recently_used_(LRU))
eviction policies. It is suitable for build systems that produce many small
object files, such as is typical for C/C++ compilation.

[Authentication](https://redis.io/commands/auth) is supported using 
`BUILDCACHE_REDIS_PASSWORD` with or without `BUILDCACHE_REDIS_USERNAME`.

Example:
```bash
$ BUILDCACHE_REMOTE=redis://my-redis-server:6379 buildcache g++ -c -O2 hello.cpp -o hello.o
```

### HTTP

The HTTP storage backend works with any HTTP server which allows `GET` and `PUT`
requests on the configured path.

Example:
```bash
$ BUILDCACHE_REMOTE=http://my-http-server:9000/my-buildcache-path buildcache g++ -c -O2 hello.cpp -o hello.o
```

### S3

[S3](https://en.wikipedia.org/wiki/Amazon_S3) is an open HTTP based protocol
that is often provided by [object storage](https://en.wikipedia.org/wiki/Object_storage)
solutions. [Amazon AWS](https://aws.amazon.com/) is one such service. An open
source alternative is [MinIO](https://min.io/).

Compared to a Redis cache, an S3 object store usually has a higher capacity and
a slightly higher performance overhead. Thus it is better suited for larger
build artifacts.

When using an S3 remote, you also need to define `BUILDCACHE_S3_ACCESS` and
`BUILDCACHE_S3_SECRET`. You will also need to create a bucket for BuildCache
in your S3 storage, and configure some retention policy (e.g. periodic LRU
eviction).

Example:
```bash
$ BUILDCACHE_REMOTE=s3://my-minio-server:9000/my-buildcache-bucket BUILDCACHE_S3_ACCESS="ABCDEFGHIJKL01234567" BUILDCACHE_S3_SECRET="sOMloNgSecretKeyThatsh0uldnotBeshownatAll" buildcache g++ -c -O2 hello.cpp -o hello.o
```

## Using with Visual Studio / MSBuild

For usage with command line MSBuild or in Visual Studio, BuildCache must be configured to be compatible with MSBuild's FileTracker.

* Set `BUILDCACHE_DIR` environment variable to `C:\ProgramData\buildcache`.
  * or [one of the folders ignored by file tracking](https://github.com/microsoft/msbuild/blob/9eb5d09e6cd262375e37a15a779d56ab274167c8/src/Utilities/TrackedDependencies/FileTracker.cs#L208).
* Create a symlink named `cl.exe` pointing to your `buildcache.exe`.
  * Alternatively, set `BUILDCACHE_IMPERSONATE` to `cl.exe`.

Additionally, several default project settings have to be changed:

* Change object file names from `$(IntDir)` to `$(IntDir)%(Filename).obj` to get one compiler invocation per source file.
  * Can be set by opening a project's properties, then *Configuration Properties*, *C/C++*, *Output Files* page, *Object File Name* setting,
  * Alternatively define the `<ObjectFileName>` property inside the `<ClCompile>` ItemDefinitionGroup in your `vcxproj` file.
* Change Debug information format to `C7 Compatible` / `OldStyle` to get all debugging information in generated obj file.
  * Can be set by opening a project's properties, then *Configuration Properties*, *C/C++*, *General* page, *Debug Information Format* setting, to `C7 Compatible (/Z7)`
  * Alternatively define the `<DebugInformationFormat>` property inside the `<ClCompile>` ItemDefinitionGroup in your `vcxproj` file to `OldStyle`.
* Since the previous step turns off compiler level parallelism, restore performance using [`MultiToolTask`](https://devblogs.microsoft.com/cppblog/improved-parallelism-in-msbuild/).
  * Can be turned on using the `<UseMultiToolTask>` property inside the `"Globals"` PropertyGroup in your `vcxproj`.
* Set `<CLToolExe>` property to the symlink created previously.
  * Also placed inside the `"Globals"` PropertyGroup in your `vcxproj`.

## Using with Cargo

To use BuildCache when compiling Rust crates with Cargo the following steps are needed:

- Set either the environment variable `RUSTC_WRAPPER`, or the key `rustc-workspace-wrapper` in the `[build]` section of the `config.toml` to `buildcache`.
- Set either the environment variable `CARGO_INCREMENTAL` to `0`, or the key `incremental` in the `[build]` section of the `config.toml` to `false`.

See https://doc.rust-lang.org/cargo/reference/config.html and https://doc.rust-lang.org/cargo/reference/environment-variables.html for further information.

Additionally, since buildcache will cache the output of building a crate, the
cached data may be significantly larger than when caching files for e.g. a C++
project. To be able to handle this, the following might be required:

- Enable `BUILDCACHE_COMPRESS`
- Increase the value of `BUILDCACHE_MAX_CACHE_SIZE`
- Increase the value of `BUILDCACHE_MAX_LOCAL_ENTRY_SIZE`.

## Statistics

Run `buildcache --show-stats` to display cache hit/miss counters. In addition
to the overall totals, statistics are tracked separately per wrapper type (e.g.
`rust`, `lua-gcc`) and per session stat ID (see `BUILDCACHE_STAT_ID` in
[configuration](configuration.md)).

### Filtering the output

Both `--show-stats` and `--zero-stats` accept an optional `PATTERN` argument,
an [ERE](https://www.gnu.org/software/grep/manual/grep.html#Regular-Expressions)
regular expression matched against stat IDs and wrapper names. Only entries
whose name matches the pattern are shown or cleared; overall totals are always
included.

```bash
# Show stats only for entries matching "rust" or the stat ID "ci-build"
buildcache --show-stats 'rust|ci-build'

# Zero only the stats accumulated under stat ID "my-feature-branch"
buildcache --zero-stats my-feature-branch
```

Omitting the filter argument shows or zeros all statistics as usual.


# Using custom Lua plugins

It is possible to extend the capabilities of BuildCache with
[Lua](https://www.lua.org/). See [lua-examples](../lua-examples/) for some
examples of Lua wrappers.

## Location of wrapper scripts

BuildCache first searches for Lua scripts in the paths given in the environment
variable `BUILDCACHE_LUA_PATH` (colon separated on POSIX systems, and semicolon
separated on Windows), and then continues searching in `$BUILDCACHE_DIR/lua`.
If no matching script file was found, BuildCache falls back to the built in
compiler wrappers (as listed above).

## Wrapper identification

The first line of a Lua based program wrapper script must be a Lua comment with
a special "match"-statement that specifies a regex that matches the name of the
program that is to be wrapped, e.g:

```Lua
-- match(gcc.*)
```

More detailed checks can be done in the optional `can_handle_command` method.

## Anatomy of a wrapper

The following methods can be implemented (see
[program_wrapper.hpp](../src/wrappers/program_wrapper.hpp) for a more detailed
documentation):

| Function | Returns | Default |
| --- | --- | --- |
| can_handle_command() | Can the wrapper handle this program? | true |
| resolve_args() | (nothing) | - |
| get_capabilities() | A list of supported capabilities | An empty table |
| get_build_files() | A table of build result files | An empty table |
| get_program_id() | A unique program identification | The MD4 hash of the program binary |
| get_relevant_arguments() | Arguments that can affect the build output | All arguments |
| get_relevant_env_vars() | Environment variables that can affect the build output | An empty table |
| get_hash_extra_content() | Extra wrapper-specific content to mix into the cache key | An empty string |
| get_input_files()\* | Get the paths to the input files for the command | And empty table |
| preprocess_source() | The preprocessed source code (e.g. for C/C++) | An empty string |
| finalize_after_hit() | (nothing) | - |
| run_for_miss() | A `sys::run_result_t` compatible table | *See note\*\** |

\*: `get_input_files` is only used in direct mode, which requires that
`direct_mode` is reported by `get_capabilities`.

\*\*: `run_for_miss`, when defined, shall run the actual command (as specified by
`m_args`) if a cache miss occurs. The return value shall be a table consisting of
`std_out`, `std_err` and `return_code` (see
[sys::run_result_t](../src/sys/sys_utils.hpp)). The default implementation is
equivalent to `bcache.run(m_args, false)`.

## Miscellaneous

All program arguments are available in the global `m_args` array (an array of
strings). `m_args[1]` is the path to the program that is being wrapped.

The original unresolved arguments (before `resolve_args()` is called) are
available in the read-only global `m_unresolved_args`. After preprocessing,
implicitly discovered input files are available in `m_implicit_input_files`.

To use Lua standard libraries (`coroutine`, `debug`, `io`, `math`, `os`,
`package`, `string`, `table` or `utf8`), you must first load them by calling
`require_std(name)`. For convenience it is possible to load all standard
libraries with `require_std("*")`, but beware that it is slower than to load
only the libraries that are actually used.

## The bcache library

There is a `bcache` library that exposes some of the internal BuildCache
functions that may be useful. To use the library, call `require_std("bcache")`.

The following functions are available (for more detailed information, look up
the corresponding C++ function documentation):

| Function | Description |
| --- | --- |
| dir_exists(path) | Check if a directory exists |
| file_exists(path) | Check if a file exists |
| get_dir_part(path) | Get the directory part of a path |
| get_extension(path) | Get the file extension of a path |
| get_file_info(path) | Get file information about a single file or directory |
| get_file_part(path, include_ext) | Get the file name part of a path |
| log_debug(str) | Print a log message with log level "DEBUG" |
| log_error(str) | Print a log message with log level "ERROR" |
| log_fatal(str) | Print a log message with log level "FATAL" |
| log_info(str) | Print a log message with log level "INFO" |
| log_warning(str) | Print a log message with log level "WARNING" |
| parse_json(str) | Parse a JSON string and return a Lua table/value |
| run(args) | Run the given command (passed as a list of arguments) |
| split_args(str) | Construct a list of arguments from a string with a shell-like format |

