-- /qompassai/dotfiles/.config/wireplumber/scripts/monitors/v4l2/create-device.lua
-- Qompass AI WirePlumber V4L2 Create-Device Monitors Script
-- Copyright (C) 2026 Qompass AI, All rights reserved
------------------------------------------------------------------------
cutils = require('common-utils') ---@type WPUtils
mutils = require('monitor-utils') ---@type WPUtils
log = Log.open_topic('s-monitors-v4l2') ---@type WPLog
config = { ---@type WPDSPConfig
  rules = Conf.get_section_as_json('monitor.v4l2.rules', Json.Array({})), ---@type WPJsonObject
}
--- Register a V4L2 camera node created by a SpaDevice.
---@param parent WPSpaDevice   -- parent spa device
---@param id integer           -- spa object id
---@param type string          -- object type (unused, kept for signature)
---@param factory string       -- factory name
---@param properties WPProperties -- node properties
---@return nil
function createV4l2camNode(parent, id, type, factory, properties)
  if false then
    local _ = type
  end
  mutils:register_cam_node(parent, id, factory, properties)
end

SimpleEventHook({
  name = 'monitor/v4l2/create-device',
  after = 'monitor/v4l2/name-device',
  interests = {
    EventInterest({
      Constraint({
        'event.type',
        '=',
        'create-v4l2-device',
      }),
    }),
  },
  execute = function(event) ---@param event WPEvent
    local properties = event:get_data('device-properties') ---@type WPProperties
    local factory = event:get_data('factory') ---@type string
    local parent = event:get_subject() ---@type WPObject
    ---@cast parent WPSpaDevice
    local id = event:get_data('device-sub-id') ---@type integer
    properties = JsonUtils.match_rules_update_properties(config.rules, properties)
    if cutils.parseBool(properties['device.disabled']) then
      log:notice('V4L2 device ' .. properties['device.name'] .. ' disabled')
      return
    end
    local device = SpaDevice(factory, properties)
    if device then
      device:connect('create-object', createV4l2camNode)
      device:activate(Feature.SpaDevice.ENABLED + Feature.Proxy.BOUND)
      parent:store_managed_object(id, device) ---@cast parent WPSpaDevice
    else
      log:warning('Failed to create \'' .. tostring(factory) .. '\' device')
    end
  end,
}):register()
