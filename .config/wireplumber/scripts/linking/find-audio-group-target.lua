-- /qompassai/dotfiles/.config/wireplumber/scripts/linking/find-audio-group-target.lua
-- Qompass AI WirePlumber Find-Audio-Group-Target Linking Script
-- Copyright (C) 2026 Qompass AI, All rights reserved
------------------------------------------------------------------------
lutils = require('linking-utils') ---@type WPUtils
cutils = require('common-utils') ---@type WPUtils
agutils = require('audio-group-utils') ---@type WPUtils
log = Log.open_topic('s-linking') ---@type WPLog
SimpleEventHook({
    name = 'linking/find-audio-group-target',
    after = 'linking/find-defined-target',
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
        local picked_target ---@type WPSessionItem|nil
        local target_can_passthrough = false ---@type boolean
        local node ---@type WPNode|WPObject|nil
        local audio_group ---@type string|nil
        log:info(
            si,
            string.format(
                'handling item %d: %s (%s)',
                si.id,
                tostring(si_props['node.name']),
                tostring(si_props['node.id'])
            )
        )
        node = si:get_associated_proxy('node')
        if node == nil then
            return
        end
        audio_group = agutils.get_audio_group(node)
        if audio_group == nil then
            return
        end
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
            local target_node = item:get_associated_proxy('node') ---@type WPNode|WPObject|nil
            if target_node then
                local target_node_props = target_node.properties ---@type WPProperties
                local target_audio_group = target_node_props['session.audio-group'] ---@type string|nil
                if target_audio_group ~= nil and target_audio_group == audio_group then
                    local passthrough_compatible, can_passthrough = lutils:checkPassthroughCompatibility(si, item)
                    if passthrough_compatible then
                        picked_target = item
                        target_can_passthrough = can_passthrough
                        break
                    else
                        log:debug(si, '... passthrough is not compatible, skip linkable')
                    end
                end
            end
        end
        if picked_target then
            log:info(
                si,
                string.format(
                    '... audio group target picked: %s (%s), can_passthrough:%s',
                    tostring(picked_target.properties['node.name']),
                    tostring(picked_target.properties['node.id']),
                    tostring(target_can_passthrough)
                )
            )
            si_flags.can_passthrough = target_can_passthrough
            event:set_data('target', picked_target)
        end
    end,
}):register()
