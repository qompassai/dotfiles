-- /qompassai/dotfiles/.config/knockoff/simple.lua
-- Qompass AI KnockOff Simple Config
-- Copyright (C) 2025 Qompass AI, All rights reserved
------------------------------------------
interfaces = {"wlp0s20f0u2"}
local function open_it(t, name)
    execute([[/usr/bin/iptables -A TCP -s %IP% -p tcp --dport {port} -j ACCEPT
sleep {open_wait}
execute("/usr/bin/iptables -D TCP -s %IP% -p tcp --dport {port} -j ACCEPT")]],
    {open_wait=10, port=8013})
end
watcher = mk_watcher {
    start = seq('simple'){ 2111, 2112, 2113, timeout=3, fails=1,
                           proceed='success' },
    success = function(t, name, cur)
        return open_it, { t, name }
    end
}
