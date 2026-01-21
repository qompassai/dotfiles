-- /qompassai/dotfiles/.config/wireplumber/scripts/monitors/bluez.lua
-- Qompass AI WirePlumber Bluez Monitor Script
-- Copyright (C) 2026 Qompass AI, All rights reserved
------------------------------------------------------------------------
COMBINE_OFFSET = 64
LOOPBACK_SOURCE_ID = 128
LOOPBACK_SINK_ID = 129
DEVICE_SOURCE_ID = 0
DEVICE_SINK_ID = 1
cutils = require("common-utils") ---@type WPUtils
log = Log.open_topic("s-monitors") ---@type WPLog
config = {}
config.seat_monitoring = Core.test_feature("monitor.bluez.seat-monitoring")
config.properties = Conf.get_section_as_properties("monitor.bluez.properties")
config.rules = Conf.get_section_as_json("monitor.bluez.rules", Json.Array {})
-- This is not a setting, it must always be enabled
config.properties["api.bluez5.connection-info"] = true
sco_source_node_properties = {} -- Properties used for previously creating a SCO source node. key: SPA device id
-- Properties used for previously creating a SCO or A2DP sink node. key: SPA device id
sco_a2dp_sink_node_properties = {}
devices_om = ObjectManager {
  Interest {
    type = "device",
  }
}
nodes_om = ObjectManager {
  Interest {
    type = "node",
    Constraint {
      "node.name", "#", "*.bluez_*put*" },
    Constraint {
      "device.id", "+" },
  }
}
--- Set the Bluetooth offload-active flag on a device.
---@param device WPDevice The PipeWire device to modify
---@param value boolean Whether offload should be active
function setOffloadActive(device, value)
  local pod = Pod.Object {
    "Spa:Pod:Object:Param:Props", "Props", bluetoothOffloadActive = value
  }
  device:set_params("Props", pod)
end

nodes_om:connect("object-added", function(_, node)
  node:connect("state-changed", function(n, old_state, cur_state)
    log:debug(string.format(
      "bluez node state changed: id=%s old=%s new=%s",
      tostring(n["bound-id"] or n.id or "unknown"),
      tostring(old_state),
      tostring(cur_state)
    ))

    local interest = Interest {
      type = "device",
      Constraint { "object.id", "=", n.properties["device.id"] },
    }
    for d in devices_om:iterate(interest) do
      setOffloadActive(d, cur_state == "running")
    end
  end)
end)
--- Create a loopback node used for SCO offload for a Bluetooth device.
---@param parent WPSpaDevice The parent SPA device
---@param id integer The SPA object id for this node
---@param type string The PipeWire object type (unused, logged for debugging)
---@param factory string The factory name used to create the SPA node
---@param properties WPProperties The node properties from PipeWire
---@return nil
function createOffloadScoNode(parent, id, type, factory, properties)
  local dev_props = parent.properties

  local args = {
    ["audio.channels"] = 1,
    ["audio.position"] = "[MONO]",
  }

  local desc =
      dev_props["device.description"]
      or dev_props["device.name"]
      or dev_props["device.nick"]
      or dev_props["device.alias"]
      or "bluetooth-device"
  -- sanitize description, replace ':' with ' '
  args["node.description"] = desc:gsub("(:)", " ")

  if factory:find("sink") then
    local capture_args = {
      ["device.id"] = parent["bound-id"],
      ["media.class"] = "Audio/Sink",
      ["node.pause-on-idle"] = false,
    }
    for k, v in pairs(properties) do
      capture_args[k] = v
    end
    local name = "bluez_output" ..
        "." .. (properties["api.bluez5.address"] or dev_props["device.name"]) .. "." .. tostring(id)
    args["node.name"] = name:gsub("([^%w_%-%.])", "_")
    args["capture.props"] = Json.Object(capture_args)
    args["playback.props"] = Json.Object {
      ["node.passive"] = true,
      ["node.pause-on-idle"] = false,
      ["state.restore-props"] = false,
    }
  elseif factory:find("source") then
    local playback_args = {
      ["device.id"] = parent["bound-id"],
      ["media.class"] = "Audio/Source",
      ["node.pause-on-idle"] = false,
    }
    for k, v in pairs(properties) do
      playback_args[k] = v
    end

    local name = "bluez_input" ..
        "." .. (properties["api.bluez5.address"] or dev_props["device.name"]) .. "." .. tostring(id)
    args["node.name"] = name:gsub("([^%w_%-%.])", "_")
    args["capture.props"] = Json.Object {
      ["node.passive"] = true,
      ["node.pause-on-idle"] = false,
      ["state.restore-props"] = false,
    }
    args["playback.props"] = Json.Object(playback_args)
  else
    log:warning(parent, "Unsupported factory: " .. factory)
    return
  end
  local args_json = Json.Object(args)      --- Transform 'args' to a json object here

  local args_string = args_json:get_data() --- and get the final JSON as a string from the json object
  local loopback_properties = {}
  local loopback = LocalModule("libpipewire-module-loopback", args_string, loopback_properties)
  parent:store_managed_object(id, loopback)
end

device_set_nodes_om = ObjectManager {
  Interest {
    type = "node",
    Constraint { "api.bluez5.set.leader", "+", type = "pw" },
  }
}

device_set_nodes_om:connect("object-added", function(_, node)
  -- Connect ObjectConfig events to the right node
  if not monitor then
    return
  end

  local interest = Interest {
    type = "device",
    Constraint { "object.id", "=", node.properties["device.id"] }
  }
  log:info("Device set node found: " .. tostring(node["bound-id"]))
  for device in devices_om:iterate(interest) do
    local device_id = device.properties["spa.object.id"]
    if not device_id then
      goto next_device
    end

    local spa_device = monitor:get_managed_object(tonumber(device_id))
    if not spa_device then
      goto next_device
    end

    local id = node.properties["card.profile.device"]
    if id ~= nil then
      log:info(".. assign to device: " .. tostring(device["bound-id"]) .. " node " .. tostring(id))
      spa_device:store_managed_object(id, node)
    end

    ::next_device::
  end
end)
--- Create a combine-stream module for a Bluetooth device set.
---@param parent WPSpaDevice The parent SPA device (not used directly, kept for signature)
---@param id integer The SPA object id for this node (not used directly)
---@param type string The object type reported by PipeWire (not used directly)
---@param factory string The factory name used to create the SPA node (not used directly)
---@param properties WPProperties Combined properties for the device set node
---@return WPLocalModule module The created combine-stream local module
function createSetNode(parent, id, type, factory, properties)
  local args = {}
  local target_class
  local stream_class
  local rules = {}
  local members_json = Json.Raw(properties["api.bluez5.set.members"])
  local channels_json = Json.Raw(properties["api.bluez5.set.channels"])
  local members = members_json:parse()
  local channels = channels_json:parse()
  if properties["media.class"] == "Audio/Sink" then
    args["combine.mode"] = "sink"
    target_class = "Audio/Sink/Internal"
    stream_class = "Stream/Output/Audio/Internal"
  else
    args["combine.mode"] = "source"
    target_class = "Audio/Source/Internal"
    stream_class = "Stream/Input/Audio/Internal"
  end

  log:info("Device set: " .. properties["node.name"])

  for _, member in pairs(members) do
    log:info("Device set member:" .. member["object.path"])
    table.insert(rules,
      Json.Object {
        ["matches"] = Json.Array {
          Json.Object {
            ["object.path"] = member["object.path"],
            ["media.class"] = target_class,
          },
        },
        ["actions"] = Json.Object {
          ["create-stream"] = Json.Object {
            ["media.class"] = stream_class,
            ["audio.position"] = Json.Array(member["channels"]),
            ["state.restore-props"] = false,
          }
        },
      }
    )
  end

  properties["node.virtual"] = false
  properties["device.api"] = "bluez5"
  properties["api.bluez5.set.members"] = nil
  properties["api.bluez5.set.channels"] = nil
  properties["api.bluez5.set.leader"] = true
  properties["audio.position"] = Json.Array(channels)
  args["combine.props"] = Json.Object(properties)
  args["stream.props"] = Json.Object {}
  args["stream.rules"] = Json.Array(rules)

  local args_json = Json.Object(args)
  local args_string = args_json:get_data()
  local combine_properties = {}
  log:info("Device set node: " .. args_string)
  return LocalModule("libpipewire-module-combine-stream", args_string, combine_properties)
end

--- Handle BlueZ device node creation for the ALSA monitor.
---@param parent WPSpaDevice The parent SPA device
---@param id integer The SPA object id for this node
---@param type string The object type (e.g. \"Adapter\", \"Device\")
---@param factory string The factory used by SPA to create the node
---@param properties WPProperties Node properties from PipeWire
---@return nil
function createNode(parent, id, type, factory, properties)
  local dev_props = parent.properties
  local parent_id = parent["bound-id"]
  local parent_spa_id = tonumber(dev_props["spa.object.id"])

  if cutils.parseBool(config.properties["bluez5.hw-offload-sco"]) and factory:find("sco") then
    createOffloadScoNode(parent, id, type, factory, properties)
    return
  end
  properties["device.id"] = parent_id -- set the device id and spa factory name; REQUIRED, do not change
  properties["factory.name"] = factory
  properties["spa.object.id"] = id
  properties["node.pause-on-idle"] = false -- set the default pause-on-idle setting

  -- set the node description
  local desc =
      dev_props["device.description"]
      or dev_props["device.name"]
      or dev_props["device.nick"]
      or dev_props["device.alias"]
      or "bluetooth-device"
  -- sanitize description, replace ':' with ' '
  properties["node.description"] = desc:gsub("(:)", " ")

  local name_prefix = ((factory:find("sink") and "bluez_output") or
    (factory:find("source") and "bluez_input" or factory))

  -- hide the source node because we use the loopback source instead
  if parent:get_managed_object(LOOPBACK_SOURCE_ID) ~= nil and
      (factory == "api.bluez5.sco.source" or
        (factory == "api.bluez5.a2dp.source" and cutils.parseBool(properties["api.bluez5.a2dp-duplex"]))) then
    properties["bluez5.loopback-target"] = true
    properties["api.bluez5.internal"] = true
    -- add 'internal' to name prefix to not be confused with loopback node
    name_prefix = name_prefix .. "_internal"
  end

  -- hide the sink node because we use the loopback sink instead
  if parent:get_managed_object(LOOPBACK_SINK_ID) ~= nil and
      (factory == "api.bluez5.sco.sink" or
        factory == "api.bluez5.a2dp.sink") then
    properties["bluez5.sink-loopback-target"] = true
    properties["api.bluez5.internal"] = true
    -- add 'internal' to name prefix to not be confused with loopback node
    name_prefix = name_prefix .. "_internal"
  end

  -- set the node name
  local name = name_prefix .. "." ..
      (properties["api.bluez5.address"] or dev_props["device.name"]) .. "." ..
      tostring(id)
  -- sanitize name
  properties["node.name"] = name:gsub("([^%w_%-%.])", "_")

  -- set priority
  if not properties["priority.driver"] then
    local priority = factory:find("source") and 2010 or 1010
    properties["priority.driver"] = priority
    properties["priority.session"] = priority
  end

  -- autoconnect if it's a stream
  if properties["api.bluez5.profile"] == "headset-audio-gateway" or
      properties["api.bluez5.profile"] == "bap-sink" or
      factory:find("a2dp.source") or factory:find("media.source") then
    properties["node.autoconnect"] = true
  end

  -- apply properties from the rules in the configuration file
  properties = JsonUtils.match_rules_update_properties(config.rules, properties)

  -- create the node; bluez requires "local" nodes, i.e. ones that run in
  -- the same process as the spa device, for several reasons

  if properties["api.bluez5.set.leader"] then
    local combine = createSetNode(parent, id, type, factory, properties)
    parent:store_managed_object(id + COMBINE_OFFSET, combine)
    parent:set_managed_pending(id)
  else
    log:info("Create node: " .. properties["node.name"] .. ": " .. factory .. " " .. tostring(id))
    if factory == "api.bluez5.sco.source" then
      properties["bluez5.loopback"] = false
      sco_source_node_properties[parent_spa_id] = properties
    elseif factory == "api.bluez5.sco.sink" or factory == "api.bluez5.a2dp.sink" then
      properties["bluez5.sink-loopback"] = false
      sco_a2dp_sink_node_properties[parent_spa_id] = properties
    end
    local node = LocalNode("adapter", properties)
    node:activate(Feature.Proxy.BOUND)
    parent:store_managed_object(id, node)
  end
end

--- Remove stored SCO properties and device-set module for a node.
---@param parent WPSpaDevice
---@param id integer
---@return nil
function removeNode(parent, id)
  local dev_props = parent.properties
  local spa_id_str = dev_props["spa.object.id"] -- spa.object.id might be missing or not numeric; handle that first
  local parent_spa_id = spa_id_str and tonumber(spa_id_str)
  if parent_spa_id == nil then
    log:debug("removeNode: no valid spa.object.id for parent, id=" .. tostring(id))
    parent:store_managed_object(id + COMBINE_OFFSET, nil) -- clear the device-set module keyed by node id
    return
  end
  local src_properties = sco_source_node_properties[parent_spa_id]
  local sink_properties = sco_a2dp_sink_node_properties[parent_spa_id]
  log:debug("Remove node: " .. tostring(id))
  if src_properties ~= nil then
    local src_id_str = src_properties["spa.object.id"]
    local src_id = src_id_str and tonumber(src_id_str)
    if src_id ~= nil and id == src_id then
      log:debug("Clear old SCO source properties")
      sco_source_node_properties[parent_spa_id] = nil
    end
  end
  if sink_properties ~= nil then
    local sink_id_str = sink_properties["spa.object.id"]
    local sink_id = sink_id_str and tonumber(sink_id_str)
    if sink_id ~= nil and id == sink_id then
      log:debug("Clear old SCO-A2DP sink properties")
      sco_a2dp_sink_node_properties[parent_spa_id] = nil
    end
  end

  parent:store_managed_object(id + COMBINE_OFFSET, nil)
end

--- Create or update a BlueZ device object.
---@param parent WPSpaDevice
---@param id integer
---@param type string
---@param factory string
---@param properties WPProperties
---@return nil
function createDevice(parent, id, type, factory, properties)
  local device = parent:get_managed_object(id)
  if not device then
    -- ensure a proper device name
    local name =
        (properties["device.name"] or
          properties["api.bluez5.address"] or
          properties["device.description"] or
          tostring(id)):gsub("([^%w_%-%.])", "_")

    if not name:find("^bluez_card%.", 1) then
      name = "bluez_card." .. name
    end
    properties["device.name"] = name

    -- set the icon name
    if not properties["device.icon-name"] then
      local icon = nil
      local icon_map = {
        -- form factor -> icon
        ["microphone"] = "audio-input-microphone",
        ["webcam"] = "camera-web",
        ["handset"] = "phone",
        ["portable"] = "multimedia-player",
        ["tv"] = "video-display",
        ["headset"] = "audio-headset",
        ["headphone"] = "audio-headphones",
        ["speaker"] = "audio-speakers",
        ["hands-free"] = "audio-handsfree",
      }
      local f = properties["device.form-factor"]
      local b = properties["device.bus"]

      icon = icon_map[f] or "audio-card"
      properties["device.icon-name"] = icon .. (b and ("-" .. b) or "")
    end

    -- initial profile is to be set by policy-device-profile.lua, not spa-bluez5
    properties["bluez5.profile"] = "off"
    properties["spa.object.id"] = id

    -- apply properties from the rules in the configuration file
    properties = JsonUtils.match_rules_update_properties(config.rules, properties)

    -- create the device
    device = SpaDevice(factory, properties)
    if device then
      device:connect("create-object", createNode)
      device:connect("object-removed", removeNode)
      parent:store_managed_object(id, device)
    else
      log:warning("Failed to create '" .. factory .. "' device")
      return
    end
  end

  log:info(parent, string.format("%d, %s (%s): %s",
    id, properties["device.description"],
    properties["api.bluez5.address"], properties["api.bluez5.connection"]))

  -- activate the device after the bluez profiles are connected
  if properties["api.bluez5.connection"] == "connected" then
    device:activate(Feature.SpaDevice.ENABLED | Feature.Proxy.BOUND)
  else
    device:deactivate(Features.ALL)
  end
end

--- Remove cached SCO properties for the given BlueZ device id.
---@param parent WPSpaDevice
---@param id integer
---@return nil
function removeDevice(parent, id)
  log:debug(string.format(
    "removeDevice: parent=%s id=%d",
    tostring(parent and parent.id or "nil"),
    id
  ))
  sco_source_node_properties[id] = nil
  sco_a2dp_sink_node_properties[id] = nil
end

--- Create and activate the BlueZ monitor.
---@return WPSpaDevice|nil monitor
function createMonitor()
  local monitor = SpaDevice("api.bluez5.enum.dbus", config.properties)
  if monitor then
    monitor:connect("create-object", createDevice)
    monitor:connect("object-removed", removeDevice)
  else
    log:notice("PipeWire's BlueZ SPA plugin is missing or broken. " ..
      "Bluetooth devices will not be supported.")
    return nil
  end
  monitor:activate(Feature.SpaDevice.ENABLED)

  return monitor
end

--- Create the loopback source module for a Bluetooth device.
---@param dev_name string The device name (used in node.name)
---@param dec_desc string Human‑readable device description
---@param dev_id integer PipeWire device id
---@return WPLocalModule module The created loopback local module
function CreateDeviceLoopbackSource(dev_name, dec_desc, dev_id)
  local args = Json.Object {
    ["capture.props"] = Json.Object {
      ["node.name"] = string.format("bluez_capture_internal.%s", dev_name),
      ["media.class"] = "Stream/Input/Audio/Internal",
      ["node.description"] =
          string.format("Bluetooth internal capture stream for %s", dec_desc),
      ["audio.channels"] = 1,
      ["audio.position"] = "[MONO]",
      ["bluez5.loopback"] = true,
      ["stream.dont-remix"] = true,
      ["node.passive"] = true,
      ["node.dont-fallback"] = true,
      ["node.linger"] = true,
      ["state.restore-props"] = false,
    },
    ["playback.props"] = Json.Object {
      ["node.name"] = string.format("bluez_input.%s", dev_name),
      ["node.description"] = string.format("%s", dec_desc),
      ["node.virtual"] = false,
      ["audio.position"] = "[MONO]",
      ["media.class"] = "Audio/Source",
      ["device.id"] = dev_id,
      ["card.profile.device"] = DEVICE_SOURCE_ID,
      ["device.routes"] = "1",
      ["priority.session"] = 2010,
      ["bluez5.loopback"] = true,
      ["filter.smart"] = true,
      ["filter.smart.target"] = Json.Object {
        ["bluez5.loopback-target"] = true,
        ["bluez5.loopback"] = false,
        ["device.id"] = dev_id
      }
    }
  }
  return LocalModule("libpipewire-module-loopback", args:get_data(), {})
end

--- Create the loopback sink module for a Bluetooth device.
---@param dev_name string  The device name used in node.name
---@param dec_desc string  Human‑readable device description
---@param dev_id integer   PipeWire device id
---@return WPLocalModule module The created loopback local module
function CreateDeviceLoopbackSink(dev_name, dec_desc, dev_id)
  local args = Json.Object {
    ["capture.props"] = Json.Object {
      ["node.name"] = string.format("bluez_output.%s", dev_name),
      ["node.description"] = string.format("%s", dec_desc),
      ["node.virtual"] = false,
      ["audio.position"] = "[FL, FR]",
      ["media.class"] = "Audio/Sink",
      ["device.id"] = dev_id,
      ["card.profile.device"] = DEVICE_SINK_ID,
      ["device.routes"] = "1",
      ["priority.session"] = 2010,
      ["bluez5.sink-loopback"] = true,
      ["filter.smart"] = true,
      ["filter.smart.target"] = Json.Object {
        ["bluez5.sink-loopback-target"] = true,
        ["bluez5.sink-loopback"] = false,
        ["device.id"] = dev_id
      }
    },
    ["playback.props"] = Json.Object {
      ["node.name"] = string.format("bluez_playback_internal.%s", dev_name),
      ["media.class"] = "Stream/Output/Audio/Internal",
      ["node.description"] =
          string.format("Bluetooth internal playback stream for %s", dec_desc),
      ["bluez5.sink-loopback"] = true,
      ["node.passive"] = true,
      ["node.dont-fallback"] = true,
      ["node.linger"] = true,
      ["state.restore-props"] = false,
    }
  }
  return LocalModule("libpipewire-module-loopback", args:get_data(), {})
end

--- Check available profiles for a BlueZ device and create loopback nodes if needed.
---@param dev WPDevice
---@return nil
function checkProfiles(dev)
  local device_id = dev["bound-id"]
  local props = dev.properties
  local device_spa_id = tonumber(props["spa.object.id"])

  -- Don't create loopback source device if autoswitch is disabled
  if not Settings.get_boolean("bluetooth.autoswitch-to-headset-profile") then
    return
  end

  local internal_id = tostring(props["spa.object.id"])

  local spa_device = monitor:get_managed_object(internal_id) --- Get the associated BT SpaDevice
  if spa_device == nil then
    return
  end
  local has_a2dpsink_profile = false -- Ignore devices that don't support both A2DP sink and HSP/HFP profiles
  local has_headset_profile = false
  for p in dev:iterate_params("EnumProfile") do
    local profile = cutils.parseParam(p, "EnumProfile")
    if profile.name:find("a2dp") and profile.name:find("sink") then
      has_a2dpsink_profile = true
    elseif profile.name:find("headset") then
      has_headset_profile = true
    end
  end
  if not has_a2dpsink_profile or not has_headset_profile then
    return
  end


  local param = Pod.Object({ --- Setup Route/Port correctly for loopback nodes
    "Spa:Pod:Object:Param:Props",
    "Props",
    params = Pod.Struct({ "bluez5.autoswitch-routes", true })
  })
  dev:set_param("Props", param)
  local source_loopback = spa_device:get_managed_object(LOOPBACK_SOURCE_ID) --- Create the source loopback device if never created before
  if source_loopback == nil then
    local dev_name = props["api.bluez5.address"] or props["device.name"]
    local dec_desc = props["device.description"] or props["device.name"]
        or props["device.nick"] or props["device.alias"] or "bluetooth-device"

    log:info("create SCO source loopback node: " .. dev_name)

    -- sanitize description, replace ':' with ' '
    dec_desc = dec_desc:gsub("(:)", " ")
    source_loopback = CreateDeviceLoopbackSource(dev_name, dec_desc, device_id)
    spa_device:store_managed_object(LOOPBACK_SOURCE_ID, source_loopback)

    -- recreate any sco source node
    local properties = sco_source_node_properties[device_spa_id]
    if properties ~= nil then
      local node_id = tonumber(properties["spa.object.id"])
      local node = spa_device:get_managed_object(node_id)
      if node ~= nil then
        log:info("Recreate node: " .. properties["node.name"] .. ": " ..
          properties["factory.name"] .. " " .. tostring(node_id))

        spa_device:store_managed_object(node_id, nil)

        properties["bluez5.loopback-target"] = true
        properties["api.bluez5.internal"] = true
        node = LocalNode("adapter", properties)
        node:activate(Feature.Proxy.BOUND)
        spa_device:store_managed_object(node_id, node)
      end
    end
  end

  local sink_loopback = spa_device:get_managed_object(LOOPBACK_SINK_ID)
  if sink_loopback == nil then
    local dev_name = props["api.bluez5.address"] or props["device.name"]
    local dec_desc = props["device.description"] or props["device.name"]
        or props["device.nick"] or props["device.alias"] or "bluetooth-device"

    log:info("create SCO-A2DP sink loopback node: " .. dev_name)

    -- sanitize description, replace ':' with ' '
    dec_desc = dec_desc:gsub("(:)", " ")
    sink_loopback = CreateDeviceLoopbackSink(dev_name, dec_desc, device_id)
    spa_device:store_managed_object(LOOPBACK_SINK_ID, sink_loopback)


    local properties = sco_a2dp_sink_node_properties[device_spa_id] -- recreate any sco-a2dp sink node
    if properties ~= nil then
      local node_id = tonumber(properties["spa.object.id"])
      local node = spa_device:get_managed_object(node_id)
      if node ~= nil then
        log:info("Recreate node: " .. properties["node.name"] .. ": " ..
          properties["factory.name"] .. " " .. tostring(node_id))

        spa_device:store_managed_object(node_id, nil)

        properties["bluez5.sink-loopback-target"] = true
        properties["api.bluez5.internal"] = true
        node = LocalNode("adapter", properties)
        node:activate(Feature.Proxy.BOUND)
        spa_device:store_managed_object(node_id, node)
      end
    end
  end
end

--- Handle parameter changes on a BlueZ device.
---@param dev WPDevice        -- The device whose params changed
---@param param_name string   -- The name of the changed parameter
---@return nil
function onDeviceParamsChanged(dev, param_name)
  if param_name == "EnumProfile" then
    checkProfiles(dev)
  end
end

devices_om:connect("object-added", function(_, dev)
  -- Ignore all devices that are not BT devices
  if dev.properties["device.api"] ~= "bluez5" then
    return
  end
  dev:connect("params-changed", onDeviceParamsChanged) -- check available profiles
  checkProfiles(dev)
end)

if config.seat_monitoring then
  logind_plugin = Plugin.find("logind")
end
if logind_plugin then
  -- if logind support is enabled, activate
  -- the monitor only when the seat is active
  ---@param seat_state string
  ---@return nil
  function startStopMonitor(seat_state)
    log:info(logind_plugin, "Seat state changed: " .. seat_state)
    if seat_state == "active" then
      monitor = createMonitor()
    elseif monitor then
      monitor:deactivate(Feature.SpaDevice.ENABLED)
      monitor = nil
    end
  end

  logind_plugin:connect("state-changed", function(p, s)
    if false then log:debug("logind sender: " .. tostring(p)) end
    startStopMonitor(s)
  end)
  nodes_om:activate()
  devices_om:activate()
  device_set_nodes_om:activate()
end
