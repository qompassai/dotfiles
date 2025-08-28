rocks_trees = {
    { name = "user", root = home .. "/.local/share/luarocks/5.2" };
}
lua_interpreter = "lua5.2";
variables = {
    LUA_DIR = home .. "/.local/share/luarocks/5.2";
    LUA_BINDIR = home .. "/.local/share/luarocks/5.2/bin";
    LUA_INCDIR = "/usr/include/lua5.2";
    LUA_LIBDIR = home .. "/.local/share/luarocks/5.2/lib";
}
