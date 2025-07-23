-- ~/.config/nix/templates/lang/lua/.luacheckrc
-- --------------------------------------------
-- Copyright (C) 2025 Qompass AI, All rights reserved
-- .luacheckrc - Luacheck configuration for Lua AI development
std = "lua51"
stds.openresty = {
    globals = {
        "_G", "_VERSION", "arg", "coroutine", "debug", "getmetatable", "io",
        "ipairs", "jit", "math", "module", "ndk", "next", "ngx", "os",
        "package", "pairs", "rawequal", "rawget", "rawlen", "rawset", "require",
        "setmetatable", "string", "table", "tonumber", "tostring", "type"
    },
    read_globals = {
        "after_each", "assert", "before_each", "dataloader", "dataset",
        "describe", "ffi", "ffi.C", "ffi.alignof", "ffi.cast", "ffi.cdef",
        "ffi.copy", "ffi.errno", "ffi.fill", "ffi.gc", "ffi.istype", "ffi.load",
        "ffi.metatype", "ffi.new", "ffi.offsetof", "ffi.sizeof", "ffi.string",
        "ffi.typeof", "finally", "it", "jit.arch", "jit.flush", "jit.off",
        "jit.on", "jit.opt", "jit.os", "jit.prngstate", "jit.status",
        "jit.version", "jit.version_num", "loss", "mock", "model",
        "ngx.crc32_long", "ngx.crc32_short", "ngx.ctx", "ngx.decode_base64",
        "ngx.encode_base64", "ngx.exec", "ngx.exit", "ngx.hmac_sha1", "ngx.log",
        "ngx.md5", "ngx.print", "ngx.re", "ngx.redirect", "ngx.req", "ngx.resp",
        "ngx.say", "ngx.sha1_bin", "ngx.shared", "ngx.socket", "ngx.timer",
        "ngx.var", "ngx.worker", "optimizer", "pending", "setup", "spy", "stub",
        "teardown", "tensor", "torch"
    }
}
std = "lua51+openresty"
include_files = {
    "*.lua", "benchmarks/**/*.lua", "examples/**/*.lua", "lua/**/*.lua",
    "src/**/*.lua", "tests/**/*.lua"
}
exclude_files = {
    "**/*_spec.lua", "**/spec/**", ".cache/**", ".luarocks/**", "logs/**",
    "lua_modules/**", "target/**"
}
max_line_length = 120
max_cyclomatic_complexity = 15
unused_args = false
unused = true
globals = {
    "_M", "AI", "Config", "Logger", "M", "ML", "Model", "Neural", "Tensor",
    "Utils", "after_each", "app", "assert", "before_each", "config", "describe",
    "it", "logger", "setup", "teardown", "utils"
}
read_globals = {
    "_G", "_VERSION", "arg", "bit", "cjson", "coroutine", "criterion", "debug",
    "ffi", "io", "jit", "lfs", "lpeg", "math", "module", "ndk", "ngx", "nn",
    "optim", "os", "package", "pl", "re", "require", "socket", "string",
    "table", "tensor", "torch"
}
ignore = {
    "211", -- Unused local variable
    "212", -- Unused argument
    "213", -- Unused loop variable
    "311", -- Value assigned to a local variable is unused
    "411", -- Redefining a local variable
    "412", -- Redefining an argument
    "421", -- Shadowing a local variable
    "422", -- Shadowing an argument
    "423" -- Shadowing a loop variable
}

fatals = {
    "111", -- Setting non-standard global variable
    "112", -- Mutating non-standard global variable
    "113" -- Accessing undefined variable
}
cache = true
color = true
ranges = true
quiet = 1
