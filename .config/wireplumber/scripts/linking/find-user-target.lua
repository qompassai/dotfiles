-- /qompassai/dotfiles/.config/wireplumber/scripts/linking/find-user-target.lua
-- Qompass AI WirePlumber Find-User-Target Linking Script
-- Copyright (C) 2026 Qompass AI, All rights reserved
------------------------------------------------------------------------
lutils = require('linking-utils')
log = Log.open_topic('s-linking') ---@type WPLog
SimpleEventHook({
    name = 'linking/sample-find-user-target',
    before = 'linking/find-defined-target',
    interests = {
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'select-target',
            }),
        }),
    },
    execute = function(event)
        local source, om, si, si_props, si_flags, target = lutils:unwrap_select_target_event(event)

        -- bypass the hook if the target is already picked up
        if target then
            return
        end
        log:info(si, 'in find-user-target')
        -- implement logic here to find a suitable target
        -- store the found target on the event,
        -- the next hooks will take care of linking
        event:set_data('target', target)
    end,
}):register()
