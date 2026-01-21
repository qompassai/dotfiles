-- /qompassai/dotfiles/.config/wireplumber/scripts/monitors/v4l2/name-Node.lua
-- Qompass AI WirePlumber V4L2 Name-Node Monitors Script
-- Copyright (C) 2026 Qompass AI, All rights reserved
--------------------------------------------------------------------------------
mutils = require('monitor-utils') ---@type WPUtils
log = Log.open_topic('s-monitors-v4l2') ---@type WPLog
SimpleEventHook({
    name = 'monitor/v4l2/name-node',
    interests = {
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'create-v4l2-device-node',
            }),
        }),
    },
    --- Process a V4L2 node creation event.
    execute = function(event) ---@param event WPEvent
        local properties = event:get_data('node-properties') ---@type WPProperties
        local parent = event:get_subject()
        local dev_props = parent.properties ---@type WPProperties
        local factory = event:get_data('factory') ---@type string
        local id = event:get_data('node-sub-id') ---@type integer
        properties['device.id'] = parent['bound-id'] ---@type string set device id/spa factory name; *DO NOT* Change
        properties['factory.name'] = factory
        properties['node.pause-on-idle'] = false --- set the default pause-on-idle setting
        local name = (factory:find('sink') and 'v4l2_output') --- set the node name
            or (factory:find('source') and 'v4l2_input' or factory)
                .. '.'
                .. (
                    dev_props['device.name']:gsub('^v4l2_device%.(.+)', '%1')
                    or dev_props['device.name']
                    or dev_props['device.nick']
                    or dev_props['device.alias']
                    or 'v4l2-device'
                )
        name = name:gsub('([^%w_%-%.])', '_') --- sanitize name
        properties['node.name'] = name
        for counter = 2, 99, 1 do -- deduplicate nodes with the same name
            if mutils.find_duplicate(parent, id, 'node.name', properties['node.name']) then
                properties['node.name'] = name .. '.' .. counter
            else
                break
            end
        end
        local desc = dev_props['device.description'] or 'v4l2-device' ---@type string node description
        desc = desc .. ' (V4L2)'
        properties['node.description'] = desc:gsub('(:)', ' ') --- sanitize description, replace ':' with ' '
        local nick = properties['node.nick'] -- set the node nick
            or dev_props['device.product.name']
            or dev_props['api.v4l2.cap.card']
            or dev_props['device.description']
            or dev_props['device.nick']
        properties['node.nick'] = nick:gsub('(:)', ' ')
        if not properties['priority.session'] then --- set priority
            local path = properties['api.v4l2.path'] or '/dev/video100'
            local dev = path:gsub('/dev/video(%d+)', '%1')
            properties['priority.session'] = 1000 - (tonumber(dev) * 10)
        end
        event:set_data('node-properties', properties)
    end,
}):register()
