-- /qompassai/dotfiles/.config/knockoff/sha2.lua
-- Qompass AI KnockOff SHA2 Config
-- Copyright (C) 2025 Qompass AI, All rights reserved
------------------------------------------
interfaces = {"wlp0s20f0u2"}
local secret = "$(pass show knockoff/sha2)"
local port = 8013
local open_wait = 10
local function open_it(_port_could_be_used_for_something)
    execute([[/usr/bin/iptables -A TCP -s %IP% -p tcp --dport {port} -j ACCEPT
sleep {open_wait}
/usr/bin/iptables -D TCP -s %IP% -p tcp --dport {port} -j ACCEPT]],
    {port=port, open_wait=open_wait})
end
watcher = mk_watcher {
    start = seq('sha2'){ secret=secret, proceed='success' },
    success = function(t, name, cur)  -- NOTE could change this of course.
        return open_it, {getmetatable(cur)[cur.m]:next()}
    end,
    prev_success = 'success'
}
