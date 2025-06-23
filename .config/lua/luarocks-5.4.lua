rocks_trees = {
    { name = "user", root = home .. "/.local/share/luarocks/5.4" };
}
lua_interpreter = "lua5.4";
variables = {
    LUA_DIR = home .. "/.local/share/luarocks/5.4";
    LUA_BINDIR = home .. "/.local/share/luarocks/5.4/bin";
    LUA_INCDIR = "/usr/include/lua5.4";
    LUA_LIBDIR = home .. "/.local/share/luarocks/5.4/lib";
}
