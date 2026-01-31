-- /qompassai/dotfiles/.config/luarocks/luarocks-5.1.lua
-- Qompass AI Lua 5.1 Luarocks config
-- Copyright (C) 2025 Qompass AI, All rights reserved
-----------------------------------------------------
local home = os_getenv('HOME')
--local lua_include = lua_root .. '/include/luajit-2.1'
local xdg_data = os_getenv('XDG_DATA_HOME') or (home .. '/.local/share')
local xdg_cache = os_getenv('XDG_CACHE_HOME') or (home .. '/.cache')
local luajit_root = xdg_data .. '/lua/luajit'
local lua51_root = xdg_data .. '/lua/5.1'
arch = 'x86_64'
build_from_rockspec = false
cache_dir = xdg_cache .. '/luarocks'
check_certificate = true
connection_timeout = 30
deploy_lib_dir = 'lib'
deploy_bin_dir = 'bin'
deps_mode = 'all'
download_method = 'curl'
encrypted_peer = true
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
git_server = 'git@github.com:'
git_use_https = false
home = home
lib_modules_dir = 'lib/lua/luajit'
local_by_default = true
lock_manifests = true
lua_interpreter = lua_root .. '/bin/luajit'
lua_modules_dir = 'share/lua/luajit'
lua_version = 'jit'
namespace = 'user'
nodeps = false
platform = 'linux'
platforms = {
    unix = true,
    linux = true,
    bsd = false,
    macosx = false,
    windows = false,
}
prefer_binary = false
rocks_servers = {
    'https://luarocks.org',
}
rocks_subdir = 'lib/luarocks/rocks-5.1'
rocks_trees = {
    {
        name = 'user',
        root = lua_root,
    },
}
ssldefault = 'https'
server_protocol = 'https'
upload = {
    server = 'https://luarocks.org',
    -- api_key = "your-api-key-here",
}
variables = {
    AR = 'llvm-ar',
    CC = 'sccache clang',
    CFLAGS = '-O3 -fPIC -Wall -Wextra -I' .. lua_include,
    CXX = 'sccache clang++',
    CXXFLAGS = '-O3 -fPIC -Wall -Wextra -stdlib=libc++ -I' .. lua_include,
    LD = 'sccache clang',
    LDFLAGS = '-L' .. lua_root .. '/lib -lluajit-5.1',
    OBJDIR = 'obj',
    RANLIB = 'llvm-ranlib',
}
verbose = true
