-- /qompassai/dotfiles/.config/wireplumber/scripts/node/suspend-node.lua
-- Qompass AI WirePlumber Node Suspend-Node Script
-- Copyright (C) 2026 Qompass AI, All rights reserved
------------------------------------------------------------------------
log = Log.open_topic('s-node') ---@type WPLog
sources = {}
SimpleEventHook({
    name = 'node/suspend-node',
    interests = {
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'node-state-changed',
            }),
            Constraint({
                'media.class',
                'matches',
                'Audio/*',
            }),
        }),
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'node-state-changed',
            }),
            Constraint({
                'media.class',
                'matches',
                'Video/*',
            }),
        }),
    },
    execute = function(event) ---@param event WPNodeEvent
        local node = event:get_subject()
        local new_state = event:get_properties()['event.subject.new-state']
        log:debug(node, 'changed state to ' .. new_state)
        local id = node['bound-id']
        if sources[id] then
            sources[id]:destroy()
            sources[id] = nil
        end
        if new_state == 'idle' or new_state == 'error' then
            local timeout = tonumber(node.properties['session.suspend-timeout-seconds']) or 5
            if timeout == 0 then
                return
            end
            sources[id] = Core.timeout_add(timeout * 1000, function()
                local active = node:get_active_features()
                if bit and bit.band(active, Feature.Proxy.BOUND) ~= 0 then
                    log:info(node, 'was idle for a while; suspending ...')
                    node:send_command('Suspend')
                end
                sources[id] = nil --- Unref the source
                return false --- false (== G_SOURCE_REMOVE) destroys the source so that this
            end) --- function does not get fired again after 5 seconds
        end
    end,
}):register()
