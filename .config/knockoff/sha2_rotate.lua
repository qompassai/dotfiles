-- /qompassai/dotfiles/.config/knockoff/sha2.lua
-- Qompass AI KnockOff SHA2 Config
-- Copyright (C) 2025 Qompass AI, All rights reserved
------------------------------------------


N=1
   cur_min=$(date +"%Y/%M/%d %H:%m)
   knockoff $your_sha2_rotate knock
   while ! try_connect_return_success; do
       knockoff $your_sha2_rotate knock -increment_n $N

       sleep 0.5  # Suppose dont entirely go nuts.

       if [ "$(date +"%Y/%M/%d %H:%m)" == $cur_min ]; then
           N=$(expr $N + 1)  # Still same minute.
       else
           N = 0  # Different minute, it will reset.
       fi
   done
interfaces = {"wlp0s20f0u2"}

local function open_it(_t, _name, port)
    execute([[
/usr/bin/iptables -A TCP -s %IP% -p tcp --dport {port} -j ACCEPT

sleep {delay}  # Provide time to access it.

# This assumes the connection stays open, if there are multiple requests, it
# will have to be longer/permanent/closed again by the application.
/usr/bin/iptables -D TCP -s %IP% -p tcp --dport {port}  -j ACCEPT
]], { port==port, delay=10})
end

local secret = "$(pass show knockoff/sha2)"

watcher = mk_watcher {
    start = seq('sha2'){ secret=secret, proceed='success',
                         increment=true, increment_n=tonumber(args.increment_n)
    },
    success = function(t, name, cur)
        local port = getmetatable(cur)[cur.m]:next()
        return open_it, {t, name, port}
    end
}
