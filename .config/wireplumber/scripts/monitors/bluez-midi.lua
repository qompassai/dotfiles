-- /qompassai/dotfiles/.config/wireplumber/scripts/monitors/bluez-midi.lua
-- Qompass AI WirePlumber Bluez-Midi Monitors Script
-- Copyright (C) 2026 Qompass AI, All rights reserved
------------------------------------------------------------------------
cutils = require('common-utils') ---@type WPUtils
log = Log.open_topic('s-monitors') ---@type WPLog
defaults = {} ---@type table
defaults.servers = {
    'bluez_midi.server',
}
config = { ---@type WPBluezMidiConfig
    seat_monitoring = Core.test_feature('monitor.bluez.seat-monitoring'),
    properties = Conf.get_section_as_properties('monitor.bluez-midi.properties'),
    servers = Conf.get_section_as_array('monitor.bluez-midi.servers', defaults.servers),
    rules = Conf.get_section_as_json('monitor.bluez-midi.rules', Json.Array({})),
} -- unique device/node name tables
node_names_table = nil ---@type table<string, boolean>|nil
id_to_name_table = nil ---@type table<integer, string>|nil
--- Set latency offset on a node in milliseconds.
---@param node WPNode
---@param offset_msec number|nil
---@return nil
function setLatencyOffset(node, offset_msec)
    if not offset_msec then
        return
    end
    local props = { 'Spa:Pod:Object:Param:Props', 'Props' }
    props.latencyOffsetNsec = tonumber(offset_msec) * 1000000
    local param = Pod.Object(props)
    log:debug(param, 'setting latency offset on ' .. tostring(node))
    node:set_param('Props', param)
end

--- Create a BlueZ MIDI node under the given parent SpaDevice.
---@param parent WPSpaDevice
---@param id integer
---@param type string
---@param factory string
---@param properties WPProperties
---@return nil
function createNode(parent, id, type, factory, properties)
    log:debug('createNode: spa type=' .. tostring(type))
    properties['factory.name'] = factory
    local desc = properties['node.description'] or 'Bluetooth MIDI' --- set the node description
    properties['node.description'] = desc:gsub('(:)', ' ') --- sanitize description, replace ':' with ' '
    local name = 'bluez_midi.' .. properties['api.bluez5.address'] -- set the node name
    name = name:gsub('([^%w_%-%.])', '_') -- sanitize name
    node_names_table = node_names_table or {} --- deduplicate nodes with the same name
    properties['node.name'] = name
    for counter = 2, 99, 1 do
        if node_names_table[properties['node.name']] ~= true then
            node_names_table[properties['node.name']] = true
            break
        end
        properties['node.name'] = name .. '.' .. counter
    end
    properties['api.glib.mainloop'] = 'true'
    properties = JsonUtils.match_rules_update_properties(config.rules, properties) --- apply properties from the rules in the configuration file
    local latency_offset = properties['node.latency-offset-msec']
    properties['node.latency-offset-msec'] = nil
    -- create the node
    local node = LocalNode('spa-node-factory', properties)
    node:activate(Feature.Proxy.BOUND)
    parent:store_managed_object(id, node)
    id_to_name_table = id_to_name_table or {}
    id_to_name_table[id] = properties['node.name']
    setLatencyOffset(node, latency_offset)
end

--- Create the BlueZ MIDI monitor SpaDevice.
---@return WPSpaDevice|nil monitor
function createMonitor()
    local monitor_props = {}
    for k, v in pairs(config.properties or {}) do
        monitor_props[k] = v
    end
    monitor_props['api.glib.mainloop'] = 'true'
    local monitor = SpaDevice('api.bluez5.midi.enum', monitor_props)
    if monitor then
        monitor:connect('object-removed', function(parent, id)
            log:debug(
                'BlueZ MIDI object removed from parent='
                    .. tostring(parent and parent.id or 'nil')
                    .. ' id='
                    .. tostring(id)
            )
            if id_to_name_table and node_names_table then
                local name = id_to_name_table[id]
                if name then
                    node_names_table[name] = nil
                end
                id_to_name_table[id] = nil
            end
        end)
    else
        log:notice('PipeWire\'s BlueZ MIDI SPA missing or broken. Bluetooth not supported.')
        return nil
    end
    node_names_table = {} --- reset the name tables to make sure names are recycled
    id_to_name_table = {}
    monitor:activate(Feature.SpaDevice.ENABLED)
    return monitor
end

--- Create BLE MIDI server nodes from configuration.
---@return WPNode[] servers
function createServers()
    local servers = {}
    local i = 1
    for k, v in pairs(config.servers) do
        log:debug('BlueZ MIDI server index=' .. tostring(k) .. ' name=' .. tostring(v))
        local node_props = {
            ['node.name'] = v,
            ['node.description'] = string.format(I18n.gettext('BLE MIDI %d'), i),
            ['api.bluez5.role'] = 'server',
            ['factory.name'] = 'api.bluez5.midi.node',
            ['api.glib.mainloop'] = 'true',
        }
        node_props = JsonUtils.match_rules_update_properties(config.rules, node_props)
        local latency_offset = node_props['node.latency-offset-msec']
        node_props['node.latency-offset-msec'] = nil
        local node = LocalNode('spa-node-factory', node_props)
        if node then
            node:activate(Feature.Proxy.BOUND)
            table.insert(servers, node)
            setLatencyOffset(node, latency_offset)
        else
            log:notice('Failed to create BLE MIDI server.')
        end
        i = i + 1
    end
    return servers
end

if config.seat_monitoring then
    logind_plugin = Plugin.find('logind') ---@type WPObject|nil
end
if logind_plugin then
    ---@return nil     -- if logind support=enabled, activate monitor only when seat is active
    function startStopMonitor(seat_state) ---@param seat_state string
        log:info(logind_plugin, 'Seat state changed: ' .. seat_state)
        if seat_state == 'active' then
            monitor = createMonitor()
            servers = createServers()
        elseif monitor then
            monitor:deactivate(Feature.SpaDevice.ENABLED)
            monitor = nil
            servers = nil
        end
    end

    logind_plugin:connect('state-changed', function(p, s)
        log:debug('logind_plugin state-changed sender=' .. tostring(p))
        startStopMonitor(s)
    end)
    startStopMonitor(logind_plugin:call('get-state'))
else
    monitor = createMonitor()
    servers = createServers()
end
