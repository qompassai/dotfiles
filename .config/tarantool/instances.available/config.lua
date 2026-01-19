-- /qompassai/dotfiles/.config/tarantool/instances.available/config.lua
-- Qompass AI Tarantool Instances Config
-- Copyright (C) 2025 Qompass AI, All rights reserved
-----------------------------------------------
-- References:  http://tarantool.org/doc/ | https://github.com/tarantool/shard/blob/master/README.md | https://github.com/tarantool/queue/blob/master/README.md | https://github.com/tarantool/expirationd/blob/master/README.md
box.cfg {
    listen = '*:3301';
    replication_source="127.0.0.1:3102";
    io_collect_interval = nil;
    readahead = 16320;
    memtx_dir = nil;
    memtx_memory = 128 * 1024 * 1024;
    memtx_min_tuple_size = 16;
    memtx_max_tuple_size = 128 * 1024 * 1024;
    memtx_snap_io_rate_limit = nil;
    vinyl_dir = nil;
    vinyl_memory = 128 * 1024 * 1024; -- 128Mb
    vinyl_cache = 128 * 1024 * 1024; -- 128Mb
    vinyl_max_tuple_size = 128 * 1024 * 1024;
    vinyl_write_threads = 2;
    wal_dir = nil;
    wal_mode = "write";
    wal_max_size = 256 * 1024 * 1024;
    checkpoint_interval = 60 * 60;
    checkpoint_count = 6;
    force_recovery = true;
    log_level = 7;
    logger = "tarantool.log";
    log_nonblock = false;
    too_long_threshold = 0.5;
     custom_proc_title = 'tarantool';
}
local function bootstrap()
    local space = box.schema.create_space('example')
    space:create_index('primary')
    box.schema.user.grant('guest', 'read,write,execute', 'universe')
      box.schema.user.create('example', { password = 'secret' })
      box.schema.user.grant('example', 'replication')
      box.schema.user.grant('example', 'read,write,execute', 'space', 'example')
end
box.once('example-1.0', bootstrap)
  local shard = require('shard')
  local shards = {
      servers = {
          { uri = [[host1.com:4301]]; zone = [[0]]; };
          { uri = [[host2.com:4302]]; zone = [[1]]; };
      };
      login = '$(pass show tarantool/user)';
      password = '$(pass show tarantool/pass)';
      redundancy = 2;
      binary = '127.0.0.1:3301';
      monitor = false;
  }
  shard.init(shards)
  local queue = require('queue')
  queue.create_tube(tube_name, 'fifottl')
  local expirationd = require('expirationd')
  local function is_expired(args, tuple)
    return true
  end
  expirationd.start("clean_all", space.id, is_expired {
    tuple_per_item = 50,
    full_scan_time = 3600
  })
