rocks_trees = {
    { name = "user", root = home .. "/.local/share/luarocks/5.3" };
}
lua_interpreter = "lua5.3";
variables = {
    LUA_DIR = home .. "/.local/share/luarocks/5.3";
    LUA_BINDIR = home .. "/.local/share/luarocks/5.3/bin";
    LUA_INCDIR = "/usr/include/lua5.3";
    LUA_LIBDIR = home .. "/.local/share/luarocks/5.3/lib";
}
