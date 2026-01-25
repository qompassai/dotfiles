-- /qompassai/dotfiles/.config/wireplumber/scripts/linking/find-best-target.lua
-- Qompass AI WirePlumber Find-Best-Target Linking Script
-- Copyright (C) 2026 Qompass AI, All rights reserved
------------------------------------------------------------------------
lutils = require('linking-utils') ---@type WPUtils
cutils = require('common-utils') ---@type WPUtils
futils = require('filter-utils') ---@type WPUtils
log = Log.open_topic('s-linking') ---@type WPLog
SimpleEventHook({
    name = 'linking/find-best-target',
    after = {
        'linking/find-defined-target',
        'linking/find-filter-target',
        'linking/find-media-role-target',
        'linking/find-default-target',
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
    }, ---@return nil
    execute = function(event) ---@param event WPEvent
        local source, om, si, si_props, si_flags, target = lutils:unwrap_select_target_event(event)
        ---@cast om WPSessionItemManager
        ---@cast si WPSessionItem
        ---@cast si_props WPProperties
        ---@cast si_flags table
        ---@cast target WPSessionItem|nil
        if source then
            log:info(source, 'select-target from source')
        end
        if target then
            return
        end

        local target_direction = cutils.getTargetDirection(si_props) ---@type 'input'|'output'
        local target_picked ---@type WPSessionItem|nil
        local target_can_passthrough = false
        local target_priority = 0 ---@type number  -- integer priority score
        local target_plugged = 0 ---@type number --integer plugged timestamp

        log:info(
            si,
            string.format('handling item: %s (%s)', tostring(si_props['node.name']), tostring(si_props['node.id']))
        )

        for item in
            om:iterate({
                type = 'SiLinkable',
                Constraint({
                    'item.node.type',
                    '=',
                    'device',
                }),
                Constraint({
                    'item.node.direction',
                    '=',
                    target_direction,
                }),
                Constraint({
                    'media.type',
                    '=',
                    si_props['media.type'],
                }),
            })
        do
            ---@cast item WPSessionItem
            local candidate = item ---@type WPSessionItem
            local candidate_props = candidate.properties ---@type WPProperties
            local candidate_node_id = candidate_props['node.id'] ---@type WPPropValue
            local si_target_node = candidate:get_associated_proxy('node') ---@type WPNode|WPObject|nil
            if not si_target_node then
                goto skip_linkable
            end
            local si_target_link_group = si_target_node.properties['node.link-group'] ---@type string|nil
            local priority = tonumber(candidate_props['priority.session']) or 0
            log:debug(
                candidate,
                string.format(
                    'Looking at: %s (%s)',
                    tostring(candidate_props['node.name']),
                    tostring(candidate_node_id)
                )
            )
            if si_target_link_group ~= nil and futils.is_filter_smart(target_direction, si_target_link_group) then
                log:debug(candidate, '... ignoring smart filter as best target')
                goto skip_linkable
            end
            if not lutils:haveAvailableRoutes(candidate_props) then
                log:debug(candidate, '... does not have routes, skip linkable')
                goto skip_linkable
            end
            local passthrough_compatible, can_passthrough = lutils:checkPassthroughCompatibility(si, candidate)
            if not passthrough_compatible then
                log:debug(candidate, '... passthrough is not compatible, skip linkable')
                goto skip_linkable
            end
            local plugged = tonumber(candidate_props['item.plugged.usec']) or 0
            log:debug(candidate, '... priority:' .. tostring(priority) .. ', plugged:' .. tostring(plugged))
            if
                not target_picked
                or priority > target_priority
                or (priority == target_priority and plugged > target_plugged)
            then
                log:debug(candidate, '... picked')
                target_picked = candidate
                target_can_passthrough = can_passthrough
                target_priority = priority
                target_plugged = plugged
            end
            ::skip_linkable::
        end
        if target_picked then
            log:info(
                si,
                string.format(
                    '... best target picked: %s (%s), can_passthrough:%s',
                    tostring(target_picked.properties['node.name']),
                    tostring(target_picked.properties['node.id']),
                    tostring(target_can_passthrough)
                )
            )
            si_flags.can_passthrough = target_can_passthrough
            event:set_data('target', target_picked)
        end
    end,
}):register()
