-- /qompassai/dotfiles/.config/wireplumber/scripts/monitors/libcamera/enumerate-device.lua
-- Qompass AI WirePlumber LibCamera Enumerate-Device Monitors Script
-- Copyright (C) 2026 Qompass AI, All rights reserved
------------------------------------------------------------------------
cutils = require('common-utils') ---@type WPUtils
log = Log.open_topic('s-monitors-libcamera') ---@type WPLog
config = {}
config.properties = Conf.get_section_as_properties('monitor.libcamera.properties')
--- Emit an event to create a libcamera device from a SpaDevice callback.
---@param parent WPSpaDevice        -- parent spa device
---@param id integer                -- spa object id
---@param type string               -- object type (unused, kept for signature)
---@param factory string            -- factory name
---@param properties WPProperties   -- device properties
---@return nil
function createCamDevice(parent, id, type, factory, properties)
    log:debug(string.format('createCamDevice: type=%s factory=%s id=%d', tostring(type), tostring(factory), id))
    source = source or Plugin.find('standard-event-source')
    local e = source:call('create-event', 'create-libcamera-device', parent, nil)
    e:set_data('device-properties', properties)
    e:set_data('factory', factory)
    e:set_data('device-sub-id', id)
    EventDispatcher.push_event(e)
end

monitor = SpaDevice('api.libcamera.enum.manager', config.properties)
if monitor then
    monitor:connect('create-object', createCamDevice)
    monitor:activate(Feature.SpaDevice.ENABLED)
else
    log:notice('PipeWire\'s libcamera SPA plugin is missing or broken. ' .. 'Some camera types may not be supported.')
end
