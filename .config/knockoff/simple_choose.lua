-- /qompassai/dotfiles/.config/knockoff/simple_choose.lua
-- Qompass AI KnockOff Simple Choose Config
-- Copyright (C) 2025 Qompass AI, All rights reserved
------------------------------------------
interfaces = {"wlp0s20f0u2"}
local function action_fun(t, name)
    print(name, t)
end
local function trigger_fun(t, name, cur)
    return action_fun, {t, name}
end
watcher = mk_watcher {
    start = seq('simple'){ 2111, 2112, 2113,
                           timeout=3, fails=6, proceed='split' },
    split = seq('split'){ [2114]='A', [2115]='B' },
    A = trigger_fun,
    B = trigger_fun,
    success = trigger_fun
}
