rocks_trees = {
    { name = "user", root = home .. "/.local/share/openresty" };
}
lua_interpreter = "/opt/openresty/luajit/bin/luajit";
variables = {
    LUA_DIR = "/opt/openresty/luajit";
    LUA_BINDIR = "/opt/openresty/luajit/bin";
    LUA_INCDIR = "/opt/openresty/luajit/include/luajit-2.1";
    LUA_LIBDIR = "/opt/openresty/luajit/lib";
}
