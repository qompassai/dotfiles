-- /qompassai/dotfiles/.config/wireplumber/scripts/monitors/libcamera/name-node.lua
-- Qompass AI WirePlumber LibCamera Name-Node Monitors Script
-- Copyright (C) 2026 Qompass AI, All rights reserved
------------------------------------------------------------------------
mutils = require('monitor-utils') ---@type WPUtils
log = Log.open_topic('s-monitors-libcamera') ---@type WPLog
SimpleEventHook({
    name = 'monitor/libcamera/name-node',
    interests = {
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'create-libcamera-device-node',
            }),
        }),
    },
    execute = function(event) ---@param event WPEvent
        local properties = event:get_data('node-properties') ---@type WPProperties
        local parent = event:get_subject() ---@type WPObject
        ---@cast parent WPSpaDevice
        local dev_props = parent.properties ---@type WPProperties
        local factory = event:get_data('factory') ---@type string
        local id = event:get_data('node-sub-id') ---@type integer
        local location = properties['api.libcamera.location'] ---@type string|nil
        properties['device.id'] = parent['bound-id'] --- set the device id and spa factory name; REQUIRED, do not change
        properties['factory.name'] = factory
        -- set the default pause-on-idle setting
        properties['node.pause-on-idle'] = false
        -- set the node name
        local name = (factory:find('sink') and 'libcamera_output')
            or (factory:find('source') and 'libcamera_input' or factory)
                .. '.'
                .. (
                    dev_props['device.name']:gsub('^libcamera_device%.(.+)', '%1')
                    or dev_props['device.name']
                    or dev_props['device.nick']
                    or dev_props['device.alias']
                    or 'libcamera-device'
                )
        name = name:gsub('([^%w_%-%.])', '_') --- sanitize name
        properties['node.name'] = name

        for counter = 2, 99, 1 do --- deduplicate nodes with the same name
            if mutils.find_duplicate(parent, id, 'node.name', properties['node.name']) then
                properties['node.name'] = name .. '.' .. counter
            else
                break
            end
        end
        --- set the node description
        local desc = dev_props['device.description'] or 'libcamera-device' ---@type string
        if location == 'front' then
            desc = I18n.gettext('Built-in Front Camera')
        elseif location == 'back' then
            desc = I18n.gettext('Built-in Back Camera')
        end
        properties['node.description'] = desc:gsub('(:)', ' ') --- sanitize description, replace ':' with ' '
        --- set the node nick
        local nick = properties['node.nick'] ---@type string
            or dev_props['device.product.name']
            or dev_props['device.description']
            or dev_props['device.nick']
        properties['node.nick'] = nick:gsub('(:)', ' ')
        if not properties['priority.session'] then --- set priority
            local priority = 700
            if location == 'external' then
                priority = priority + 150
            elseif location == 'front' then
                priority = priority + 100
            elseif location == 'back' then
                priority = priority + 50
            end
            properties['priority.session'] = priority
        end
        event:set_data('node-properties', properties)
    end,
}):register()
