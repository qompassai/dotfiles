-- /qompassai/dotfiles/.config/wireplumber/scripts/linking/find-default-target.lua
-- Qompass AI WirePlumber Find-Default-Target Linking Script
-- Copyright (C) 2026 Qompass AI, All rights reserved
------------------------------------------------------------------------
lutils = require('linking-utils') ---@type WPUtils
log = Log.open_topic('s-linking') ---@type WPLog
SimpleEventHook({
    name = 'linking/find-default-target',
    after = {
        'linking/find-defined-target',
        'linking/find-filter-target',
        'linking/find-media-role-target',
        'linking/find-media-role-sink-target',
    },
    before = 'linking/prepare-link',
    interests = {
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'select-target',
            }),
        }),
    },
    execute = function(event) ---@param event WPEvent
        local source, om, si, si_props, si_flags, target = lutils:unwrap_select_target_event(event)
        if target then
            return
        end
        if source then
            log:info(source, 'select-target from source')
        end
        local candidates = om:lookup({
            type = 'SiLinkable',
            Constraint({
                'media.class',
                'c',
                'Audio/Sink',
                'Audio/Source',
            }),
        })

        if candidates then
            log:info(
                si,
                string.format('ObjectManager returned candidate: %s', tostring(candidates.properties['node.name']))
            )
        end
        local target_picked = false
        log:info(
            si,
            string.format('handling item: %s (%s)', tostring(si_props['node.name']), tostring(si_props['node.id']))
        )
        target = lutils.findDefaultLinkable(si) ---@type WPSessionItem|nil
        local can_passthrough ---@type boolean
        local passthrough_compatible ---@type boolean

        if target then
            passthrough_compatible, can_passthrough = lutils:checkPassthroughCompatibility(si, target)
            if lutils:canLink(si_props, target) and passthrough_compatible then
                target_picked = true
            end
        end
        if target_picked and target ~= nil then
            log:info(
                si,
                string.format(
                    '... default target picked: %s (%s), can_passthrough:%s',
                    tostring(target.properties['node.name']),
                    tostring(target.properties['node.id']),
                    tostring(can_passthrough)
                )
            )
            si_flags.can_passthrough = can_passthrough
            event:set_data('target', target)
        end
    end,
}):register()
