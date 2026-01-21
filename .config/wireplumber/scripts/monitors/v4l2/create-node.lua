-- /qompassai/dotfiles/.config/wireplumber/scripts/monitors/v4l2/create-node.lua
-- Qompass AI WirePlumber V4L2 Create-Node Monitors Script
-- Copyright (C) 2026 Qompass AI, All rights reserved
--------------------------------------------------------------------------------
cutils = require('common-utils') ---@type WPUtils
mutils = require('monitor-utils') ---@type WPUtils
log = Log.open_topic('s-monitors-v4l2') ---@type WPLog
config = { ---@type WPDSPConfig
    rules = Conf.get_section_as_json('monitor.v4l2.rules', Json.Array({})), ---@type WPJsonObject
}
--- Handle V4L2 node creation and registration
SimpleEventHook({
    name = 'monitor/v4l2/create-node',
    after = 'monitor/v4l2/name-node',
    interests = {
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'create-v4l2-device-node',
            }),
        }),
    },
    execute = function(event) ---@param event WPEvent
        local properties = event:get_data('node-properties') ---@type WPProperties
        local parent = event:get_subject() ---@type WPObject
        ---@cast parent WPSpaDevice
        local id = event:get_data('node-sub-id') ---@type integer
        local factory = event:get_data('factory') ---@type string
        properties = JsonUtils.match_rules_update_properties(config.rules, properties) --- apply properties from rules defined in JSON .conf file
        if cutils.parseBool(properties['node.disabled']) then
            log:notice('V4L2 node ' .. properties['node.name'] .. ' disabled (factory=' .. factory .. ')')
            return
        end
        properties['node.name'] = (properties['node.name'] or 'v4l2_node') ..
        '.' .. factory:gsub('([^%w_%-%.])', '_')                                                                       --- include factory in node name so it is actually used
        local node = Node('spa-node-factory', properties)
        node:activate(Feature.Proxy.BOUND)
        parent:store_managed_object(id, node) ---@cast parent WPSpaDevice
    end,
}):register()
