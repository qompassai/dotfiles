-- /qompassai/dotfiles/.config/luarocks/luarocks-luajit.lua
-- Qompass AI Luarocks LuaJIT Config
-- Copyright (C) 2025 Qompass AI, All rights reserved
-----------------------------------------------------
local home = os.getenv('HOME') or ''
local xdg_data = os.getenv('XDG_DATA_HOME') or (home .. '/.local/share')
local xdg_cache = os.getenv('XDG_CACHE_HOME') or (home .. '/.cache')
local lua_root = xdg_data .. '/lua/luajit'
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
external_deps_subdirs = {
    bin = 'bin',
    lib = 'lib',
    include = 'include',
}
home = home
lib_modules_dir = 'lib/lua/5.1'
local_by_default = true
lock_manifests = true
lua_interpreter = lua_root .. '/bin/lua'
lua_modules_dir = 'share/lua/5.1'
lua_version = 'jit'
nodeps = false
platform = 'unix'
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
    -- api_key = '$dawg',
}
variables = {
    AR = 'llvm-ar',
    CC = 'sccache clang',
    CFLAGS = '-O3 -fPIC -Wall -Wextra -I' .. lua_root .. '/include',
    CXX = 'sccache clang++',
    CXXFLAGS = '-O3 -fPIC -Wall -Wextra -stdlib=libc++ -I' .. lua_root .. '/include',
    LD = 'sccache clang',
    LDFLAGS = '-L' .. lua_root .. '/lib -lluajit-5.1 ',
    LUA = lua_root .. '/bin/lua',
    LUA_DIR = lua_root,
    LUA_BINDIR = lua_root .. '/bin',
    LUA_INCDIR = lua_root .. '/include',
    LUA_LIBDIR = lua_root .. '/lib',
    OBJDIR = 'obj',
    RANLIB = 'llvm-ranlib',
}
verbose = true
