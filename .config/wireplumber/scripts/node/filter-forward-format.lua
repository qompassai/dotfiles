-- /qompassai/dotfiles/.config/wireplumber/scripts/node/filter-forward-format.lua
-- Qompass AI WirePlumber Node Filter Forward Format Script
-- Copyright (C) 2026 Qompass AI, All rights reserved
------------------------------------------------------------------------
lutils = require('linking-utils') ---@type WPLinkingUtils
log = Log.open_topic('s-node') ---@type WPLog
--- Find the link-group peer device for a filter stream
---@return WPSessionItem|nil
function findAssociatedLinkGroupNode(si) ---@param si WPSessionItem
    local si_props = si.properties
    local link_group = si_props['node.link-group']
    if link_group == nil then
        return nil
    end
    local std_event_source = Plugin.find('standard-event-source')
    local om = std_event_source:call('get-object-manager', 'session-item') ---@cast om WPObjectManager
    local assoc_direction = cutils.getTargetDirection(si_props) --- get the associated media class
    local assoc_media_class = si_props['media.type'] .. (assoc_direction == 'input' and '/Sink' or '/Source')
    for assoc_si in
        om:iterate({ --- find the linkable with same link group and matching assoc media class
            type = 'SiLinkable',
        })
    do
        local assoc_props = assoc_si.properties ---@cast assoc_si WPSessionItem
        local assoc_link_group = assoc_props['node.link-group']
        if assoc_link_group == link_group and assoc_media_class == assoc_props['media.class'] then
            return assoc_si
        end
    end
    return nil
end

--- React to adapter ports state changes and forward the new format to the device.
---@param old_state string
---@param new_state string
function onLinkGroupPortsStateChanged(si, old_state, new_state) ---@param si WPSessionItem
    local si_props = si.properties
    if new_state ~= 'configured' then --- only handle items with configured ports state
        return
    end
    if old_state == 'configured' then
        log:debug(si, 'ports already configured, ignoring transition on ' .. si_props['node.name'])
        return
    end
    log:info(si, 'ports format changed on ' .. si_props['node.name'])
    local si_device = findAssociatedLinkGroupNode(si) --- find associated device
    if si_device ~= nil then
        local device_node_name = si_device.properties['node.name']
        local f, m = si:get_ports_format() --- get the stream format
        log:info(si_device, 'unregistering ' .. device_node_name) --- unregister the device
        si_device:remove()
        log:info(si_device, 'setting new format in ' .. device_node_name) --- set new format in the device
        si_device:set_ports_format(f, m, function(item, e)
            if e ~= nil then
                log:warning(item, 'failed to configure ports in ' .. device_node_name .. ': ' .. e)
            end
            log:info(item, 'registering ' .. device_node_name) --- register back the device
            item:register()
        end)
    end
end

SimpleEventHook({
    name = 'node/filter-forward-format',
    interests = {
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'session-item-added',
            }),
            Constraint({
                'event.session-item.interface',
                '=',
                'linkable',
            }),
            Constraint({
                'item.factory.name',
                'c',
                'si-audio-adapter',
                'si-node',
            }),
            Constraint({
                'media.class',
                '#',
                'Stream/*',
                type = 'pw-global',
            }),
        }),
    },
    --- Forward filters ports format to virtual devices if enabled, only listen for ports state changed on audio filter streams
    execute = function(event) ---@param event WPEvent
        local si = event:get_subject() ---@cast si WPSessionItem
        if Settings.get_boolean('node.filter.forward-format') then
            local si_props = si.properties
            local link_group = si_props['node.link-group']
            local si_flags = lutils:get_flags(si.id)
            if
                si_flags.ports_state_signal ~= true
                and si_props['item.factory.name'] == 'si-audio-adapter'
                and si_props['item.node.type'] == 'stream'
                and link_group ~= nil
            then
                si:connect('adapter-ports-state-changed', onLinkGroupPortsStateChanged)
                si_flags.ports_state_signal = true
                log:info(si, 'listening ports state changed on ' .. si_props['node.name'])
            end
        end
    end,
}):register()
