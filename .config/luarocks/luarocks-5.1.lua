-- /qompassai/dotfiles/.config/luarocks/luarocks-5.1.lua
-- Qompass AI Lua 5.1 Luarocks config
-- Copyright (C) 2025 Qompass AI, All rights reserved
-----------------------------------------------------
local home = os_getenv('HOME')
local xdg_data = os_getenv('XDG_DATA_HOME') or (home .. '/.local/share')
local xdg_cache = os_getenv('XDG_CACHE_HOME') or (home .. '/.cache')
local luajit_root = xdg_data .. '/lua/luajit'
local lua51_root = xdg_data .. '/lua/5.1'
accept_unknown_fields = false
arch = 'x86_64'
build_from_rockspec = false
cache = {
    luajit_version_checked = true,
}
cache_dir = xdg_cache .. '/luarocks'
cache_fail_timeout = 86400
cache_timeout = 60
check_certificate = true
check_certificates = true
cmake_generator = 'Ninja'
config_files = {
    nearest = '/home/phaedrus/.config/luarocks/luarocks-5.1.lua',
    system = {
        found = false,
        file = '/home/phaedrus/.config/luarocks/luarocks-5.1.lua',
    },
    user = {
        found = true,
        file = '/home/phaedrus/.config/luarocks/luarocks-5.1.lua',
    },
}
connection_timeout = 30
deploy_bin_dir = 'bin'
deploy_lib_dir = 'lib'
--deploy_lib_dir = '/home/phaedrus/.local/share/lua/luajit/lib/lua/jit'
deploy_lua_dir = 'share/lua/jit'
deps_mode = 'all'
disabled_servers = {}
download_method = 'curl'
encrypted_peer = true
export_path_separator = ':'
external_deps_dirs = {
    home .. '/.local',
    '/usr/local',
    '/usr',
}
external_deps_patterns = {
    bin = {
        '?',
    },
    lib = {
        'lib?.a',
        'lib?.so',
        'lib?.so.*',
        '?.a',
        '?.so',
    },
    include = {
        '?.h',
        '?/*.h',
    },
}
external_deps_subdirs = {
    bin = 'bin',
    lib = 'lib',
    include = 'include',
}
external_lib_extension = 'so'
fs_use_modules = true
gcc_rpath = true
git_server = 'git@github.com:'
git_use_https = false
home = home
--hometree = '/home/phaedrus/'
hooks_enabled = true
lib_extension = 'so'
lib_modules_dir = 'lib/lua/luajit'
link_lua_explicitly = false
local_by_default = true
local_cache = xdg_cache
lock_manifests = false
lua_extension = 'lua'
lua_found = true
lua_interpreter = '/usr/bin/luajit'
lua_modules_dir = 'share/lua/luajit'
lua_modules_path = 'share/lua/jit'
lua_version = '5.1'
namespace = 'user'
nodeps = false
no_manifest = false
obj_extension = 'o'
platform = 'linux'
platforms = {
    unix = true,
    linux = true,
    bsd = false,
    macosx = false,
    windows = false,
}
prefer_binary = false
processor = 'x86_64'
target_cpu = 'x86_64'
rocks_dir = luajit_root .. '/lib/luarocks/rocks-5.1'
rocks_servers = {
    'https://luarocks.org',
}
rocks_subdir = 'lib/luarocks/rocks-5.1'
rocks_trees = {
    {
        name = 'luajit',
        root = luajit_root,
    },
    {
        name = 'lua51',
        root = lua51_root,
    },
}
runtime_external_deps_patterns = {
    bin = {
        '?',
    },
    lib = {
        'lib?.so',
        'lib?.so.*',
    },
    include = {
        '?.h',
    },
}
runtime_external_deps_subdirs = {
    bin = 'bin',
    include = 'include',
    lib = {
        'lib64',
        'lib',
    },
}
server_protocol = 'https'
ssldefault = 'https'
static_lib_extension = 'a'
sysconfdir = '/home/phaedrus/.local/share/lua/luajit/lib/luarocks/rocks-5.1'
target_cpu = 'x86_64'
upload = {
    api_version = '1',
    server = 'https://luarocks.org',
    tool_version = '1.0.0',
}
user_agent = 'LuaRocks/3.12.1 x86_64'
variables = {
    AR = 'llvm-ar',
    CC = 'sccache clang',
    CFLAGS = '-O3 -fPIC -Wall -Wextra',
    --CMAKE = 'cmake',
    --CURL = 'curl',
    CXX = 'sccache clang++',
    CXXFLAGS = '-O3 -fPIC -Wall -Wextra -stdlib=libc++',
    --HG = 'hg',
    LD = 'sccache clang',
    LDFLAGS = '-L' .. luajit_root .. '/lib',
    --LIB_EXTENSION = 'so',
    --LIBFLAG = '-shared',
    LS = 'ls',
    --LUA = '/usr/bin/lua5.1',
    --LUA_BINDIR = '/usr/bin',
    --LUA_DIR = '/usr',
    --LUA_INCDIR = '/usr/include/lua5.1',
    --LUA_LIBDIR_FILE = 'liblua.so',
    --LUA_VERSION = '5.1',
    OBJDIR = 'obj',
    RANLIB = 'llvm-ranlib',
    --RM = 'rm',
    --RMDIR = 'rmdir',
    --RSYNCFLAGS = '--exclude=.git -Oavz',
    --SCP = 'SCP',
    --SSCM = 'sscm',
    --TOUCH = 'touch',
    --UNZIP = 'unzip -n',
}
verbose = true
web_browser = 'xdg-open'
wrapper_suffix = ''
