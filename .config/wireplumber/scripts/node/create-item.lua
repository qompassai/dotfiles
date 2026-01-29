-- /qompassai/dotfiles/.config/wireplumber/scripts/node/create-item.lua
-- Qompass AI WirePlumber Node Create-Item Script
-- Copyright (C) 2026 Qompass AI, All rights reserved
------------------------------------------------------------------------
cutils = require('common-utils') ---@type WPUtils
log = Log.open_topic('s-node') ---@type WPLog
items = {}
---@return WPProperties
function configProperties(node) ---@param node WPNode
    local properties = node.properties or {} ---@type WPProperties
    node.properties = properties
    local media_class = properties['media.class'] or ''
    local factory_name = properties['factory.name'] or ''
    if not properties['media.type'] then
        for _, i in ipairs({
            'Audio',
            'Video',
            'Midi',
        }) do
            if media_class:find(i) then
                properties['media.type'] = i
                break
            end
        end
    end
    properties['item.node'] = node
    properties['item.node.direction'] = cutils.mediaClassToDirection(media_class)
    properties['item.node.type'] = media_class:find('^Stream/') and 'stream' or 'device'
    properties['item.plugged.usec'] = GLib.get_monotonic_time()
    properties['item.features.no-dsp'] = Settings.get_boolean('node.features.audio.no-dsp')
    properties['item.features.monitor'] = Settings.get_boolean('node.features.audio.monitor-ports')
    properties['item.features.control-port'] = Settings.get_boolean('node.features.audio.control-port')
    properties['item.features.mono'] = (factory_name == 'api.alsa.pcm.sink' or factory_name == 'api.bluez5.a2dp.sink')
        and Settings.get_boolean('node.features.audio.mono')
    properties['node.id'] = node['bound-id']
    local default_role = Settings.get('node.stream.default-media-role')
    if default_role ~= nil then
        ---@cast default_role WPJsonObject
        local role_str = default_role:parse() ---@type string
        properties['media.role'] = properties['media.role'] or role_str
    end
    return properties
end

AsyncEventHook({
    name = 'node/create-item',
    interests = {
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'node-added',
            }),
            Constraint({
                'media.class',
                '#',
                'Stream/*',
                type = 'pw-global',
            }),
        }),
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'node-added',
            }),
            Constraint({
                'media.class',
                '#',
                'Video/*',
                type = 'pw-global',
            }),
        }),
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'node-added',
            }),
            Constraint({
                'media.class',
                '#',
                'Audio/*',
                type = 'pw-global',
            }),
            Constraint({
                'wireplumber.is-virtual',
                '-',
                type = 'pw',
            }),
        }),
    },
    steps = {
        start = {
            next = 'register',
            execute = function(event, transition)
                local node = event:get_subject() ---@cast node WPNode
                local id = node.id ---@type integer?
                if id == nil then
                    transition:return_error('node has no id')
                    return
                end
                local item
                local item_type
                local media_class = node.properties['media.class']
                if string.find(media_class, 'Audio') then
                    item_type = 'si-audio-adapter'
                else
                    item_type = 'si-node'
                end
                log:info(node, 'creating item for node -> ' .. item_type)
                item = SessionItem(item_type)
                items[id] = item
                local props = configProperties(node) ---@type WPProperties
                if not item:configure(props) then
                    transition:return_error('failed to configure item for node ' .. tostring(id))
                    return
                end
                item:activate(Features.ALL, function(_, e) --- activate item
                    if e then
                        transition:return_error('failed to activate item: ' .. tostring(e))
                    else
                        transition:advance()
                    end
                end)
            end,
        },
        register = {
            next = 'none',
            ---@param event WPEvent
            execute = function(event, transition) ---@param transition WPAsyncTransition
                local node = event:get_subject() ---@cast node WPNode
                local bound_id = node['bound-id']
                local item = items[node.id]
                log:info(item, 'activated item for node ' .. tostring(bound_id))
                item:register()
                transition:advance()
            end,
        },
    },
}):register()
SimpleEventHook({
    name = 'node/destroy-item',
    interests = {
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'node-removed',
            }),
            Constraint({
                'media.class',
                '#',
                'Stream/*',
                type = 'pw-global',
            }),
        }),
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'node-removed',
            }),
            Constraint({
                'media.class',
                '#',
                'Video/*',
                type = 'pw-global',
            }),
        }),
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'node-removed',
            }),
            Constraint({
                'media.class',
                '#',
                'Audio/*',
                type = 'pw-global',
            }),
            Constraint({
                'wireplumber.is-virtual',
                '-',
                type = 'pw',
            }),
        }),
    },
    execute = function(event) ---@param event WPEvent
        local node = event:get_subject() ---@cast node WPNode
        local id = node.id ---@type integer?
        if not id then
            return
        end
        local item = items[id]
        if item then
            item:remove()
            items[id] = nil
        end
    end,
}):register()
function reconfigureAudioAdapters() ---@return nil
    local ids = {} ---@type integer[]
    for id, item in pairs(items) do
        local si_props = item.properties
        if si_props['item.factory.name'] == 'si-audio-adapter' then
            table.insert(ids, id)
        end
    end
    for _, id in pairs(ids) do
        local item = items[id]
        local node = item:get_associated_proxy('node') ---@cast node WPNode
        log:info(item, 'Started re-configuring audio adapter')
        items[id] = nil
        item:remove()
        if not item:configure(configProperties(node)) then
            log:warning(item, 'Could not re-configure audio adapter')
            goto skip_item
        end
        items[id] = item
        item:activate(Features.ALL, function(si, e)
            if e then
                log:warning(si, 'Could not re-activate audio adapter')
            else
                log:info(si, 'Successfully re-activated audio adapter')
                si:register()
            end
        end)
        ::skip_item::
    end
end

Settings.subscribe('node.features.audio.*', function()
    reconfigureAudioAdapters()
end)
