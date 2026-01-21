-- /qompassai/dotfiles/.config/wireplumber/scripts/monitors/libcamera/name-device.lua
-- Qompass AI WirePlumber LibCamera Enumerate-Device Monitors Script
-- Copyright (C) 2026 Qompass AI, All rights reserved
------------------------------------------------------------------------
mutils = require('monitor-utils') ---@type WPUtils
log = Log.open_topic('s-monitors-libcamera') ---@type WPLog
SimpleEventHook({
    name = 'monitor/libcamera/name-device',
    interests = {
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'create-libcamera-device',
            }),
        }),
    },
    --- Process a libcamera device creation event.
    execute = function(event) ---@param event WPEvent
        local parent = event:get_subject() ---@cast parent WPSpaDevice
        local properties = event:get_data('device-properties') ---@type WPProperties
        local id = event:get_data('device-sub-id') ---@type integer
        local name = 'libcamera_device.' --- Build base device name from properties or id.
            .. (properties['device.name'] or properties['device.bus-id'] or properties['device.bus-path'] or tostring(
                id
            )):gsub('([^%w_%-%.])', '_')
        properties['device.name'] = name
        -- deduplicate devices with the same name
        for counter = 2, 99, 1 do
            if mutils.find_duplicate(parent, id, 'device.name', properties['device.name']) then
                properties['device.name'] = name .. '.' .. counter
            else
                break
            end
        end
        properties['device.description'] = properties['device.description'] -- ensure the device has a description
            or properties['device.product.name']
            or 'Unknown device'
        event:set_data('device-properties', properties)
    end,
}):register()
