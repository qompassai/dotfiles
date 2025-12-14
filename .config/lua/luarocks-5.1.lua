rocks_trees = {
    { name = "user", root = home .. "/.local/share/luarocks/5.1" };
}
lua_interpreter = "lua5.1";
variables = {
    LUA_DIR = home .. "/.local/share/luarocks/5.1";
    LUA_BINDIR = home .. "/.local/share/luarocks/5.1/bin";
    LUA_INCDIR = "/usr/include/lua5.1";
    LUA_LIBDIR = home .. "/.local/share/luarocks/5.1/lib";
}
