-- /qompassai/dotfiles/.config/wireplumber/scripts/monitors/v4l2/name-device.lua
-- Qompass AI WirePlumber V4L2 Name-Device Monitors Script
-- Copyright (C) 2026 Qompass AI, All rights reserved
--------------------------------------------------------------------------------
mutils = require('monitor-utils') ---@type WPUtils
log = Log.open_topic('s-monitors-v4l2') ---@type WPLog
SimpleEventHook({
    name = 'monitor/v4l2/name-device',
    interests = {
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'create-v4l2-device',
            }),
        }),
    },
    --- Process a V4L2 device creation event.
    execute = function(event) ---@param event WPEvent
        local properties = event:get_data('device-properties') ---@type WPProperties
        local parent = event:get_subject() ---@type WPObject
        local id = event:get_data('device-sub-id') ---@type integer
        local name = 'v4l2_device.' --- Build base device name from properties or id
            .. (properties['device.name'] or properties['device.bus-id'] or properties['device.bus-path'] or tostring(
                id
            )):gsub('([^%w_%-%.])', '_')
        properties['device.name'] = name
        for counter = 2, 99, 1 do --- deduplicate devices with the same name
            if mutils.find_duplicate(parent, id, 'device.name', properties['device.name']) then
                properties['device.name'] = name .. '.' .. counter
            else
                break
            end
        end
        properties['device.description'] = properties['device.description'] --- ensure device has description
            or properties['device.product.name']
            or 'Unknown device'
        event:set_data('device-properties', properties)
    end,
}):register()
