-- /qompassai/dotfiles/.config/wireplumber/scripts/monitors/v4l2/enumerate-device.lua
-- Qompass AI WirePlumber V4L2 Enumerate-Device Monitors Script
-- Copyright (C) 2026 Qompass AI, All rights reserved
--------------------------------------------------------------------------------
cutils = require('common-utils') ---@type WPUtils
log = Log.open_topic('s-monitors-v4l2') ---@type WPLog
config = { ---@type WPV4L2Config
    properties = Conf.get_section_as_properties('monitor.v4l2.properties'), ---@type WPProperties
}
--- Emit an event to create a V4L2 device from a SpaDevice callback.
---@param parent WPSpaDevice      # parent SpaDevice that raised the callback
---@param id integer              # spa object id for the device
---@param type string             # object type (kept for signature; not used directly)
---@param factory string          # factory name used to create the device
---@param properties WPProperties # device properties as reported by PipeWire
---@return nil
function createCamDevice(parent, id, type, factory, properties)
    log:debug(
        string.format(
            'createCamDevice: parent=%s id=%d type=%s factory=%s',
            tostring(parent and parent.id or 'nil'),
            id,
            tostring(type),
            tostring(factory)
        )
    )
    source = source or
    Plugin.find('standard-event-source')                    --- Standard-event-source is used to re-emit a higher-level event
    local e = source:call('create-event', 'create-v4l2-device', parent, nil)
    e:set_data('device-properties', properties)
    e:set_data('factory', factory)
    e:set_data('device-sub-id', id)
    EventDispatcher.push_event(e)
end

monitor = SpaDevice('api.v4l2.enum.udev', config.properties) ---@type WPSpaDevice|nil
if monitor then
    monitor:connect('create-object', createCamDevice)
    monitor:activate(Feature.SpaDevice.ENABLED)
else
    log:notice('PipeWire\'s V4L2 SPA plugin is missing or broken. ' .. 'Some camera types may not be supported.')
end
