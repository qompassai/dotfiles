rocks_trees = {
    { name = "user", root = home .. "/.local/share/luarocks/luajit" };
}
lua_interpreter = "luajit";
variables = {
    LUA_DIR = home .. "/.local/share/luarocks/luajit";
    LUA_BINDIR = home .. "/.local/share/luarocks/luajit/bin";
    LUA_INCDIR = "/usr/include/luajit-2.1";
    LUA_LIBDIR = home .. "/.local/share/luarocks/luajit/lib";
}
