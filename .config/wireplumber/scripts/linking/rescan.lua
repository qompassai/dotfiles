-- /qompassai/dotfiles/.config/wireplumber/scripts/linking/rescan.lua
-- Qompass AI WirePlumber Rescan Linking Script
-- Copyright (C) 2026 Qompass AI, All rights reserved
------------------------------------------------------------------------
lutils = require('linking-utils')
cutils = require('common-utils') ---@type WPUtils
futils = require('filter-utils') ---@type WPUtils
log = Log.open_topic('s-linking')
handles = {}
handles.rescan_enabled = true
handles.timeout_source = nil
---@param si WPSessionItem
---@param om WPSessionItemManager
---@param handle_nonstreams boolean|nil
---@return boolean
function lutils:checkFilter(si, om, handle_nonstreams)
    if handle_nonstreams then
        log:debug('checkFilter om=' .. tostring(om))
        return true
    end
    local node = si:get_associated_proxy('node')
    if not node then
        return true
    end
    local link_group = node:get_property('node.link-group')
    if link_group == nil then
        return true
    end
    local direction = cutils.getTargetDirection(si.properties)
    if not futils.is_filter_smart(direction, link_group) then
        return true
    end
    return not futils.is_filter_disabled(direction, link_group)
end

---@param si WPSessionItem
---@param om WPSessionItemManager
---@param handle_nonstreams boolean|nil
---@return boolean valid
---@return WPProperties|nil si_props
function checkLinkable(si, om, handle_nonstreams)
    if si:get_property('item.node.type') ~= 'stream' and not handle_nonstreams then
        return false
    end
    if not lutils:checkFilter(si, om, handle_nonstreams or false) then
        return false
    end

    return true
end

---@param si WPSessionItem|WPObject
---@param om WPSessionItemManager
function unhandleLinkable(si, om)
    ---@cast si WPSessionItem
    if not checkLinkable(si, om, true) then
        return
    end
    local si_id = si.id
    log:info(si, string.format('unhandling item %d', si_id))
    for silink in
        om:iterate({
            type = 'SiLink',
        })
    do
        local silink_props = silink.properties
        local out_id = silink_props:get_int('out.item.id')
        local in_id = silink_props:get_int('in.item.id')
        if out_id == si_id or in_id == si_id then
            local in_flags = lutils:get_flags(in_id)
            local out_flags = lutils:get_flags(out_id)
            if out_id == si_id and in_flags.peer_id == out_id then
                in_flags.peer_id = nil
            elseif in_id == si_id and out_flags.peer_id == in_id then
                out_flags.peer_id = nil
            end
            if silink_props:get_boolean('is.role.policy.link') then
                lutils.clearPriorityMediaRoleLink(silink)
            end
            silink:remove()
            log:info(silink, '... link removed')
        end
    end
    lutils:clear_flags(si_id)
end

SimpleEventHook({
    name = 'linking/linkable-removed',
    interests = {
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'session-item-removed',
            }),
            Constraint({
                'event.session-item.interface',
                '=',
                'linkable',
            }),
        }),
    },
    execute = function(event) ---@param event WPSessionItemEvent
        local si = event:get_subject()
        local source = event:get_source()
        local om = source:call('get-object-manager', 'session-item')
        unhandleLinkable(si, om)
    end,
}):register()
SimpleEventHook({
    name = 'linking/linkable-added-immediate',
    before = 'linking/rescan-trigger',
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
        }),
    },
    execute = function(event)
        local si = event:get_subject() ---@cast si WPSessionItem
        local source = event:get_source()
        local om = source:call('get-object-manager', 'session-item')
        if not checkLinkable(si, om, false) then
            return
        end
        local node = si:get_associated_proxy('node')
        if not node then
            return
        end
        local link_group = node:get_property('node.link-group')
        if link_group then
            local direction = cutils.getTargetDirection(si.properties)
            if futils.is_filter_smart(direction, link_group) then
                return
            end
        end
        local autoconnect = si:get_property('node.autoconnect')
        if autoconnect ~= 'true' then
            return
        end
        if si:get_property('item.node.type') ~= 'stream' then
            return
        end
        source:call('push-event', 'select-target', si, nil)
    end,
}):register()
---@return nil
function handleLinkables(source) ---@param source WPObject
    local om = source:call('get-object-manager', 'session-item')
    for si in om:iterate({ type = 'SiLinkable' }) do
        if not checkLinkable(si, om) then ---@cast si WPSessionItem
            goto skip_linkable
        end
        local si_props = si.properties
        local autoconnect = si_props:get_boolean('node.autoconnect')
        if not autoconnect then
            log:debug(si, tostring(si_props['node.name']) .. ' does not need to be autoconnected')
            goto skip_linkable
        end
        source:call('push-event', 'select-target', si, nil)
        ::skip_linkable::
    end
end

SimpleEventHook({
    name = 'linking/rescan',
    interests = {
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'rescan-for-linking',
            }),
        }),
    },
    execute = function(event)
        local source = event:get_source()
        local om = source:call('get-object-manager', 'session-item')
        log:info('rescanning...')
        for si in
            om:iterate({
                type = 'SiLinkable',
                Constraint({
                    'node.link-group',
                    '+',
                }),
            })
        do
            local node = si:get_associated_proxy('node')
            local link_group = node:get_property('node.link-group')
            local direction = cutils.getTargetDirection(si.properties)
            if futils.is_filter_smart(direction, link_group) and futils.is_filter_disabled(direction, link_group) then
                unhandleLinkable(si, om)
            end
        end

        handleLinkables(source)
    end,
}):register()
SimpleEventHook({
    name = 'linking/rescan-trigger',
    interests = {
        EventInterest({
            Constraint({
                'event.type',
                'c',
                'session-item-added',
                'session-item-removed',
            }),
            Constraint({
                'event.session-item.interface',
                '=',
                'linkable',
            }),
        }),
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'device-params-changed',
            }),
            Constraint({
                'event.subject.param-id',
                'c',
                'Route',
                'EnumRoute',
            }),
        }),
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'metadata-changed',
            }),
            Constraint({
                'metadata.name',
                '=',
                'default',
            }),
            Constraint({
                'event.subject.key',
                'c',
                'default.audio.source',
                'default.audio.sink',
                'default.video.source',
            }),
        }),
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'metadata-changed',
            }),
            Constraint({
                'metadata.name',
                '=',
                'filters',
            }),
        }),
    },
    execute = function(event)
        if handles.rescan_enabled then
            local source = event:get_source()
            source:call('schedule-rescan', 'linking')
        end
    end,
}):register()
SimpleEventHook({
    name = 'linking/session-item-added',
    before = 'linking/rescan-trigger',
    interests = {
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'session-item-added',
            }),
        }),
    },
    execute = function(event)
        local props = event:get_properties()
        log:debug(nil, string.format('rescan timeout cleared for event type=%s', tostring(props['event.type'])))
        if handles.timeout_source ~= nil then
            handles.timeout_source:destroy()
            handles.timeout_source = nil
        end
        handles.rescan_enabled = true
    end,
}):register()

SimpleEventHook({
    name = 'linking/bluez-session-item-removed',
    before = 'linking/rescan-trigger',
    interests = {
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'session-item-removed',
            }),
            Constraint({
                'device.api',
                '=',
                'bluez5',
            }),
        }),
    },
    execute = function(event) ---@param event WPEvent
        local si = event:get_subject() ---@cast si WPSessionItem
        local source = event:get_source()
        local si_id = si and si.id
        local props = si and si.properties
        local dev_name = props and props['device.name'] or props and props['node.name']
        if handles.timeout_source ~= nil then
            handles.timeout_source:destroy()
            handles.timeout_source = nil
        end
        handles.rescan_enabled = false
        handles.timeout_source = Core.timeout_add(2000, function()
            handles.timeout_source = nil
            handles.rescan_enabled = true
            if dev_name then
                log:info(
                    nil,
                    string.format(
                        'bluez item removed (id=%s, name=%s), scheduling linking rescan',
                        tostring(si_id),
                        tostring(dev_name)
                    )
                )
            else
                log:info(nil, 'bluez item removed, scheduling linking rescan')
            end
            source:call('schedule-rescan', 'linking')
            return false
        end)
    end,
}):register()
---@param enable boolean|nil
---@return nil
function handleMoveSetting(enable)
    if (not handles.move_hook) and (enable == true) then
        handles.move_hook = SimpleEventHook({
            name = 'linking/rescan-trigger-on-target-metadata-changed',
            interests = {
                EventInterest({
                    Constraint({
                        'event.type',
                        '=',
                        'metadata-changed',
                    }),
                    Constraint({
                        'metadata.name',
                        '=',
                        'default',
                    }),
                    Constraint({
                        'event.subject.key',
                        'c',
                        'target.object',
                        'target.node',
                    }),
                }),
            },
            execute = function(event)
                local source = event:get_source()
                source:call('schedule-rescan', 'linking')
            end,
        })
        handles.move_hook:register()
    elseif handles.move_hook and (enable == false) then
        handles.move_hook:remove()
        handles.move_hook = nil
    end
end

Settings.subscribe('linking.allow-moving-streams', function()
    handleMoveSetting(Settings.get_boolean('linking.allow-moving-streams'))
end)
handleMoveSetting(Settings.get_boolean('linking.allow-moving-streams'))
