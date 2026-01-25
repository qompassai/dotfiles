-- /qompassai/dotfiles/.config/wireplumber/scripts/linking/find-user-target.lua
-- Qompass AI WirePlumber Find-User-Target Linking Script
-- Copyright (C) 2026 Qompass AI, All rights reserved
------------------------------------------------------------------------
lutils = require('linking-utils') ---@type WPUtils
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
    execute = function(event) ---@param event WPEvent
        local source, om, si, si_props, si_flags, target = lutils:unwrap_select_target_event(event)
        ---@cast om WPSessionItemManager
        ---@cast si WPSessionItem
        ---@cast si_props WPProperties
        ---@cast si_flags table
        ---@cast target WPSessionItem|nil
        if source then
            log:info(source, string.format('find-user-target from source id=%s', tostring(source.id)))
        end
        if target then
            return
        end
        local app_name = si_props['application.name'] or si_props['node.name'] ---@type string|nil
        log:info(
            si,
            string.format(
                'find-user-target for app: %s (node.id=%s)',
                tostring(app_name),
                tostring(si_props['node.id'])
            )
        )
        local preferred_target_name = si_props['session.preferred-target-node'] ---@type string|nil
        local picked_target ---@type WPSessionItem|nil
        if preferred_target_name then
            for item in
                om:iterate({
                    type = 'SiLinkable',
                    Constraint({
                        'item.node.type',
                        '=',
                        'device',
                    }),
                    Constraint({
                        'media.type',
                        '=',
                        si_props['media.type'],
                    }),
                })
            do
                ---@cast item WPSessionItem
                local node = item:get_associated_proxy('node') ---@type WPNode|WPObject|nil
                if node then
                    local node_name = node.properties['node.name'] ---@type string|nil
                    if node_name == preferred_target_name then
                        log:info(si, string.format('find-user-target picked preferred node: %s', tostring(node_name)))
                        picked_target = item
                        break
                    end
                end
            end
        end
        if not picked_target then
            picked_target = lutils.findDefaultLinkable(si)
            if picked_target then
                log:info(
                    si,
                    string.format(
                        'find-user-target fell back to default target: %s',
                        tostring(picked_target.properties['node.name'])
                    )
                )
            end
        end
        if picked_target then
            si_flags.user_selected = true
            event:set_data('target', picked_target)
        end
    end,
}):register()
