-- /qompassai/dotfiles/.config/wireplumber/scripts/monitors/libcamera/create-device.lua
-- Qompass AI WirePlumber LibCamera Create-Device Monitors Script
-- Copyright (C) 2026 Qompass AI, All rights reserved
------------------------------------------------------------------------
cutils = require('common-utils') ---@type WPUtils
mutils = require('monitor-utils') ---@type WPUtils
log = Log.open_topic('s-monitors-libcamera') ---@type WPLog
config = {}
config.rules = Conf.get_section_as_json('monitor.libcamera.rules', Json.Array({}))
--- Create a libcamera node for a given SpaDevice object.
---@param parent WPSpaDevice  -- parent spa device
---@param id integer          -- spa object id
---@param type string         -- object type (unused, kept for signature)
---@param factory string      -- factory name
---@param properties WPProperties -- node properties
---@return nil
function createLibcamNode(parent, id, type, factory, properties)
    if false then
        log:debug('createLibcamNode type=' .. tostring(type))
    end
    mutils:register_cam_node(parent, id, factory, properties)
end

SimpleEventHook({
    name = 'monitor/libcamera/create-device',
    after = 'monitor/libcamera/name-device',
    interests = {
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'create-libcamera-device',
            }),
        }),
    },
    execute = function(event) ---@param event WPEvent
        local properties = event:get_data('device-properties') ---@type WPProperties
        local factory = event:get_data('factory')
        local parent = event:get_subject() ---@type WPObject
        ---@cast parent WPSpaDevice
        local id = event:get_data('device-sub-id') ---@type integer
        properties = JsonUtils.match_rules_update_properties(config.rules, properties) --- apply properties from rules defined in JSON .conf file
        if cutils.parseBool(properties['device.disabled']) then
            log:notice('libcam device ' .. properties['device.name'] .. ' disabled')
            return
        end
        local device = SpaDevice(factory, properties)
        if device then
            device:connect('create-object', createLibcamNode)
            device:activate(Feature.SpaDevice.ENABLED + Feature.Proxy.BOUND)
            parent:store_managed_object(id, device) ---@cast parent WPSpaDevice
        else
            log:warning('Failed to create \'' .. factory .. '\' device')
        end
    end,
}):register()
