-- /qompassai/dotfiles/.config/wireplumber/scripts/monitors/libcamera/create-node.lua
-- Qompass AI WirePlumber LibCamera Create-Device Monitors Script
-- Copyright (C) 2026 Qompass AI, All rights reserved
------------------------------------------------------------------------
cutils = require('common-utils') ---@type WPUtils
mutils = require('monitor-utils')
log = Log.open_topic('s-monitors-libcamera') ---@type WPLog
config = { ---@type WPDSPConfig
    rules = Conf.get_section_as_json('node.filter-graph.rules', Json.Array({})), ---@type WPJsonObject
}
SimpleEventHook({
    name = 'monitor/libcamera/create-node',
    after = 'monitor/libcamera/name-node',
    interests = {
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'create-libcamera-device-node',
            }),
        }),
    },
    execute = function(event)
        local properties = event:get_data('node-properties')
        local parent = event:get_subject()
        local id = event:get_data('node-sub-id')
        properties = JsonUtils.match_rules_update_properties(config.rules, properties)
        if cutils.parseBool(properties['node.disabled']) then
            log:notice('libcam node' .. properties['node.name'] .. ' disabled')
            return
        end
        local node = Node('spa-node-factory', properties)
        node:activate(Feature.Proxy.BOUND)
        ---@cast parent WPSpaDevice
        parent:store_managed_object(id, node)
    end,
}):register()
