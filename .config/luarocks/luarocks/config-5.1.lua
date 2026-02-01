-- LuaRocks configuration

rocks_trees = {
   { name = "user", root = home .. "/.luarocks" };
   { name = "system", root = "/home/phaedrus/.local/share/lua/luajit" };
}
variables = {
   LUA_DIR = "/usr";
   LUA_INCDIR = "/usr/include/luajit-2.1";
   LUA_BINDIR = "/usr/bin";
   LUA_VERSION = "5.1";
   LUA = "/usr/bin/lua5.1";
}
