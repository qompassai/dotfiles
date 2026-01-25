-- find-media-role-sink-target.lua
-- Qompass AI Wireplumber Find-Media-Role-Sink-Target Linking Config
-- Copyright (C) 2026 Qompass AI, All rights reserved
-- ----------------------------------------------------------------
lutils = require('linking-utils') ---@type WPUtils
cutils = require('common-utils') ---@type WPUtils
log = Log.open_topic('s-linking') ---@type WPLog
SimpleEventHook({
    name = 'linking/find-media-role-sink-target',
    after = {
        'linking/find-defined-target',
        'linking/find-media-role-target',
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
        local _, om, si, si_props, _, target = lutils:unwrap_select_target_event(event)
        local node_name = si_props['node.name'] ---@type string|nil
        local target_direction = cutils.getTargetDirection(si_props) ---@type 'input'|'output'
        local media_class = si_props['media.class'] ---@type string
        local link_group = si_props['node.link-group'] ---@type string
        local is_virtual = si_props['node.virtual'] ---@type string
        log:info(
            si,
            string.format(
                'Lookup for \'%s\' (%s) / \'%s\' / \'%s\'',
                node_name,
                tostring(si_props['node.id']),
                media_class,
                link_group
            )
        )
        if target or media_class ~= 'Stream/Output/Audio' or not is_virtual or link_group == nil then
            return
        end
        local input_node = om:lookup({
            type = 'SiLinkable',
            Constraint({
                'media.class',
                '=',
                'Audio/Sink',
            }),
            Constraint({
                'node.link-group',
                '=',
                link_group,
            }),
        })
        if input_node == nil then
            log:warning(si, string.format('No input node for %s found', link_group))
            return
        end
        local target_name = input_node.properties['policy.role-based.preferred-target'] ---@type string
        if target_name == nil then
            return
        end
        local si_target = om:lookup({
            type = 'SiLinkable',
            Constraint({
                'item.factory.name',
                'c',
                'si-audio-adapter',
                'si-node',
            }),
            Constraint({
                'node.name',
                '=',
                target_name,
            }),
        })
        if si_target == nil then
            si_target = om:lookup({
                type = 'SiLinkable',
                Constraint({
                    'item.factory.name',
                    'c',
                    'si-audio-adapter',
                    'si-node',
                }),
                Constraint({
                    'node.nick',
                    '=',
                    target_name,
                }),
                Constraint({
                    'item.node.direction',
                    '=',
                    target_direction,
                }),
            })
        end
        if si_target then
            log:info(
                si,
                string.format(
                    '... role based sink target picked: %s (%s)',
                    tostring(si_target.properties['node.name']),
                    tostring(si_target.properties['node.id'])
                )
            )
            event:set_data('target', si_target)
        end
    end,
}):register()
