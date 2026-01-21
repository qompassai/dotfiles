-- /qompassai/dotfiles/.config/wireplumber/scripts/linking/rescan.lua
-- Qompass AI WirePlumber Re-Scanning Linking Script
-- Copyright (C) 2026 Qompass AI, All rights reserved
------------------------------------------------------------------------
lutils = require('linking-utils') ---@type WPUtils
cutils = require('common-utils') ---@type WPUtils
futils = require('filter-utils')
log = Log.open_topic('s-linking') ---@type WPLog
handles = {} ---@type table
handles.rescan_enabled = true
handles.timeout_source = nil
--- Check whether a linkable item should be handled based on filter settings.
---@param si WPSessionItem
---@param om WPSessionItemManager
---@param handle_nonstreams boolean
---@return boolean
function checkFilter(si, om, handle_nonstreams)
    if false then
        log:debug('checkFilter om=' .. tostring(om))
    end
    if handle_nonstreams then -- always handle filters if handle_nonstreams is true, even if it is disabled
        return true
    end
    local node = si:get_associated_proxy('node') -- always return true if this is not a filter
    local link_group = node.properties['node.link-group']
    if link_group == nil then
        return true
    end
    local direction = cutils.getTargetDirection(si.properties)
    if not futils.is_filter_smart(direction, link_group) then -- always handle filters that are not smart
        return true
    end
    return not futils.is_filter_disabled(direction, link_group) --- dont handle smart filters that are disabled
end

--- Check if a session item is linkable and return its properties if so.
---@param si WPSessionItem
---@param om WPSessionItemManager
---@param handle_nonstreams boolean|nil
---@return boolean valid
---@return WPProperties|nil si_props
function checkLinkable(si, om, handle_nonstreams)
    local si_props = si.properties
    if not si_props or (si_props['item.node.type'] ~= 'stream' and not handle_nonstreams) then -- For the rest of them, only handle stream session items
        return false, si_props
    end
    if not checkFilter(si, om, handle_nonstreams or false) then
        return false, si_props
    end
    return true, si_props
end

--- Remove links and flags associated with a linkable session item.
---@param si WPSessionItem|WPObject
function unhandleLinkable(si, om) ---@param om WPSessionItemManager
    local si_id = si.id
    local valid, si_props = checkLinkable(si, om, true)
    if not valid then
        return
    end
    log:debug(si, 'unhandleLinkable props node.name=' .. tostring(si_props and si_props['node.name']))
    log:info(si, string.format('unhandling item %d', si_id))
    -- iterate over all the links in the graph and
    -- remove any links associated with this item
    for silink in om:iterate({ type = 'SiLink' }) do
        local out_id = tonumber(silink.properties['out.item.id'])
        local in_id = tonumber(silink.properties['in.item.id'])

        if out_id == si_id or in_id == si_id then
            local in_flags = lutils:get_flags(in_id)
            local out_flags = lutils:get_flags(out_id)

            if out_id == si_id and in_flags.peer_id == out_id then
                in_flags.peer_id = nil
            elseif in_id == si_id and out_flags.peer_id == in_id then
                out_flags.peer_id = nil
            end

            if cutils.parseBool(silink.properties['is.role.policy.link']) then
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
    execute = function(event)
        local si = event:get_subject()
        local source = event:get_source()
        if not source then
            return
        end
        local om = source:call('get-object-manager', 'session-item')
        unhandleLinkable(si, om)
    end,
}):register()
--- Scan all linkable session items and schedule linking where needed.
---@param source WPObject
---@return nil
function handleLinkables(source)
    local om = source:call('get-object-manager', 'session-item')
    for si in
    om:iterate({
        type = 'SiLinkable',
    })
    do
        local valid, si_props = checkLinkable(si, om)
        if not valid then
            goto skip_linkable
        end
        local autoconnect = cutils.parseBool(si_props['node.autoconnect']) -- check if we need to link this node at all
        if not autoconnect then
            log:debug(si, tostring(si_props['node.name']) .. ' does not need to be autoconnected')
            goto skip_linkable
        end
        source:call('push-event', 'select-target', si, nil) -- push event to find target and link

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
        for si in -- always unlink all filters that are smart and disabled
        om:iterate({
            type = 'SiLinkable',
            Constraint({
                'node.link-group',
                '+',
            }),
        })
        do
            local node = si:get_associated_proxy('node')
            if not node then
                return
            end
            local link_group = node.properties['node.link-group']
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
        -- on linkable added or removed, where linkable is adapter or plain node
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
        -- on device Routes changed
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
        -- on any "default" target changed
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
        -- on any "filters" metadata changed
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
        -- clear timeout source, if any
        if handles.timeout_source ~= nil then
            handles.timeout_source:destroy()
            handles.timeout_source = nil
        end

        -- Always enable rescan when any node is added
        handles.rescan_enabled = true
    end,
}):register()

-- Stop rescan for 2 seconds if BT item was removed. This avoids audio
-- being played on internal nodes for a few seconds while the BT device is
-- switching profiles.
SimpleEventHook({
    name = 'linking/bluez-session-item-removed',
    before = 'linking/rescan-trigger',
    interests = {
        EventInterest({
            Constraint({ 'event.type', '=', 'session-item-removed' }),
            Constraint({ 'device.api', '=', 'bluez5' }),
        }),
    },
    execute = function(event)
        local si = event:get_subject()
        local si_props = si.properties
        local source = event:get_source()

        -- clear timeout source, if any
        if handles.timeout_source ~= nil then
            handles.timeout_source:destroy()
            handles.timeout_source = nil
        end

        -- disable rescan
        handles.rescan_enabled = false
        handles.timeout_source = Core.timeout_add(2000, function() --- re-enable rescan after 2 seconds
            handles.timeout_source = nil
            handles.rescan_enabled = true
            source:call('schedule-rescan', 'linking')
        end)
    end,
}):register()
--- Enable or disable rescan trigger when target metadata changes.
---@param enable boolean
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
