-- /qompassai/dotfiles/.config/wireplumber/scripts/node/create-item.lua
-- Qompass AI WirePlumber Node Create-Item Script
-- Copyright (C) 2026 Qompass AI, All rights reserved
------------------------------------------------------------------------
cutils = require('common-utils') ---@type WPUtils
log = Log.open_topic('s-node') ---@type WPLog
items = {}
---Configure properties for a node used to create a session item.
---@return WPProperties
function configProperties(node) ---@param node WPNode
    local properties = node.properties
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
                local id = node.id
                local item
                local item_type
                local media_class = node.properties['media.class']
                if string.find(media_class, 'Audio') then
                    item_type = 'si-audio-adapter'
                else
                    item_type = 'si-node'
                end
                log:info(node, 'creating item for node -> ' .. item_type)
                item = SessionItem(item_type) --- create item
                items[id] = item
                if not item:configure(configProperties(node)) then --- configure item
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
        local id = node.id
        if items[id] then
            items[id]:remove()
            items[id] = nil
        end
    end,
}):register()
--- Re-configure all existing audio adapter session items when audio features change.
function reconfigureAudioAdapters() ---@return nil
    local ids = {} ---@type integer[]
    for id, item in pairs(items) do --- Get the Id of all session items that are audio adapters
        local si_props = item.properties
        if si_props['item.factory.name'] == 'si-audio-adapter' then
            table.insert(ids, id)
        end
    end
    for _, id in pairs(ids) do --- Re-configure all audio adapters
        local item = items[id]
        local node = item:get_associated_proxy('node') ---@cast node WPNode
        log:info(item, 'Started re-configuring audio adapter')
        items[id] = nil --- Remove the session item so that it is unlinked
        item:remove()
        if not item:configure(configProperties(node)) then --- Configure the session item
            log:warning(item, 'Could not re-configure audio adapter')
            goto skip_item
        end
        items[id] = item --- Activate the session item so that it is linked again
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
