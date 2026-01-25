-- /qompassai/dotfiles/.config/wireplumber/scripts/linking/get-filter-from-target.lua
-- Qompass AI WirePlumber Get-Filter-From-Target Linking Script
-- Copyright (C) 2026 Qompass AI, All rights reserved
------------------------------------------------------------------------
lutils = require('linking-utils') ---@type WPUtils
cutils = require('common-utils')
futils = require('filter-utils')
log = Log.open_topic('s-linking')
SimpleEventHook({
    name = 'linking/get-filter-from-target',
    after = {
        'linking/find-defined-target',
        'linking/find-filter-target',
        'linking/find-media-role-target',
        'linking/find-default-target',
        'linking/find-best-target',
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
    execute = function(event)
        local source, om, si, si_props, si_flags, target = lutils:unwrap_select_target_event(event)
        local _ = source
        local _om = om
        if target == nil or lutils.is_role_policy_target(si_props, target.properties) then
            return
        end
        local node = si:get_associated_proxy('node')
        if not node then
            return
        end
        local node_props = node.properties
        local link_group = node_props['node.link-group']
        local target_direction = cutils.getTargetDirection(si.properties)
        if link_group ~= nil and futils.is_filter_smart(target_direction, link_group) then
            return
        end
        local target_node = target:get_associated_proxy('node')
        if not target_node then
            return
        end
        local target_node_props = target_node.properties
        local target_audio_group = target_node_props['session.audio-group']
        if target_audio_group ~= nil then
            return
        end
        local target_link_group = target_node_props['node.link-group']
        if target_link_group ~= nil and si_flags.has_defined_target then
            if
                futils.is_filter_smart(target_direction, target_link_group)
                and not futils.is_filter_disabled(target_direction, target_link_group)
                and futils.is_filter_targetable(target_direction, target_link_group)
            then
                return
            end
        end
        local media_type = si_props['media.type']
        local filter_target = futils.get_filter_from_target(target_direction, media_type, target)
        if filter_target ~= nil then
            target = filter_target
            log:info(si, '... got filter for given target')
        elseif filter_target == nil and not si_flags.has_defined_target then
            filter_target = futils.get_filter_from_target(target_direction, media_type, nil)
            if filter_target ~= nil then
                target = filter_target
                log:info(si, '... got default filter for given target')
            end
        end
        local target_picked = false
        local can_passthrough, passthrough_compatible
        if target ~= nil then
            passthrough_compatible, can_passthrough = lutils:checkPassthroughCompatibility(si, target)
            if lutils:canLink(si_props, target) and passthrough_compatible then
                target_picked = true
            end
        end
        if target_picked and target ~= nil then
            log:info(
                si,
                string.format(
                    '... target picked: %s (%s), can_passthrough:%s',
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
