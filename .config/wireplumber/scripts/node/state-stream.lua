-- /qompassai/dotfiles/.config/wireplumber/scripts/node/state-stream.lua
-- Qompass AI WirePlumber Node State-Stream Script
-- Copyright (C) 2026 Qompass AI, All rights reserved
------------------------------------------------------------------------
cutils = require('common-utils') ---@type WPUtils
log = Log.open_topic('s-node') ---@type WPLog
config = { ---@type WPDSPConfig
    rules = Conf.get_section_as_json('node.filter-graph.rules', Json.Array({})), ---@type WPJsonObject
}
state = nil --- the state storage
state_table = nil
rs_metadata = nil --- Support for the "System Sounds" volume control in pavucontrol
restore_stream_hook = SimpleEventHook({ --- hook to restore stream properties & target
    name = 'node/restore-stream',
    interests = {
        EventInterest({ --- match stream nodes
            Constraint({
                'event.type',
                '=',
                'node-added',
            }),
            Constraint({
                'media.class',
                'matches',
                'Stream/*',
            }),
        }),
        EventInterest({ --- and device nodes that are not associated with any routes
            Constraint({
                'event.type',
                '=',
                'node-added',
            }),
            Constraint({
                'media.class',
                'matches',
                'Audio/*',
            }),
            Constraint({
                'device.routes',
                'is-absent',
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
                'matches',
                'Audio/*',
            }),
            Constraint({
                'device.routes',
                'equals',
                '0',
            }),
        }),
    },
    execute = function(event)
        local node = event:get_subject() ---@cast node WPNode
        local stream_props = node.properties ---@type WPProperties
        stream_props = JsonUtils.match_rules_update_properties(config.rules, stream_props)
        local key = formKey(stream_props)
        if not key then
            return
        end
        local stored_values = getStoredStreamProps(key) or {}
        if
            Settings.get_boolean('node.stream.restore-props') --- restore node Props (volumes, channelMap, etc...)
            and stream_props['state.restore-props'] ~= 'false'
        then
            local props = {
                'Spa:Pod:Object:Param:Props',
                'Props',
                volume = stored_values.volume,
                mute = stored_values.mute,
                channelVolumes = stored_values.channelVolumes ~= nil and stored_values.channelVolumes
                    or buildDefaultChannelVolumes(node),
                channelMap = stored_values.channelMap,
            }
            if props.channelVolumes then -- convert arrays to Spa Pod
                table.insert(props.channelVolumes, 1, 'Spa:Float')
                props.channelVolumes = Pod.Array(props.channelVolumes)
            end
            if props.channelMap then
                table.insert(props.channelMap, 1, 'Spa:Enum:AudioChannel')
                props.channelMap = Pod.Array(props.channelMap)
            end
            if props.volume or (props.mute ~= nil) or props.channelVolumes or props.channelMap then
                log:info(node, 'restore values from ' .. key)
                local param = Pod.Object(props)
                log:debug(param, 'setting props on ' .. tostring(stream_props['node.name']))
                node:set_param('Props', param)
            end
        end
        if Settings.get_boolean('node.stream.restore-target') and stream_props['state.restore-target'] ~= 'false' then --- restore the node's link target on metadata
            if stored_values.target then
                local target_in_props = stream_props['target.object'] or stream_props['node.target'] -- check first if there is a defined target in the node's properties
                if not target_in_props then -- and skip restoring if this is the case (#335)
                    local source = event:get_source()
                    local nodes_om = source:call('get-object-manager', 'node')
                    local metadata_om = source:call('get-object-manager', 'metadata')
                    local target_node = nodes_om:lookup({
                        Constraint({
                            'node.name',
                            '=',
                            stored_values.target,
                            type = 'pw',
                        }),
                    })
                    local metadata = metadata_om:lookup({
                        Constraint({
                            'metadata.name',
                            '=',
                            'default',
                        }),
                    })
                    if target_node and metadata then
                        metadata:set(
                            node['bound-id'],
                            'target.object',
                            'Spa:Id',
                            target_node.properties['object.serial']
                        )
                    end
                else
                    log:debug(
                        node,
                        'Not restoring the target for '
                            .. tostring(stream_props['node.name'])
                            .. '  because it is already set to '
                            .. target_in_props
                    )
                end
            end
        end
    end,
})
store_stream_props_hook = SimpleEventHook({ -- store stream properties on the state file
    name = 'node/store-stream-props',
    interests = {
        EventInterest({ --- match stream nodes
            Constraint({
                'event.type',
                '=',
                'node-params-changed',
            }),
            Constraint({
                'event.subject.param-id',
                '=',
                'Props',
            }),
            Constraint({
                'media.class',
                'matches',
                'Stream/*',
            }),
        }),
        EventInterest({ --- and device nodes that are not associated with any routes
            Constraint({
                'event.type',
                '=',
                'node-params-changed',
            }),
            Constraint({
                'event.subject.param-id',
                '=',
                'Props',
            }),
            Constraint({
                'media.class',
                'matches',
                'Audio/*',
            }),
            Constraint({
                'device.routes',
                'is-absent',
            }),
        }),
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'node-params-changed',
            }),
            Constraint({
                'event.subject.param-id',
                '=',
                'Props',
            }),
            Constraint({
                'media.class',
                'matches',
                'Audio/*',
            }),
            Constraint({
                'device.routes',
                'equals',
                '0',
            }),
        }),
    },
    execute = function(event)
        local node = event:get_subject() ---@cast node WPNode
        local stream_props = node.properties ---@type WPProperties
        stream_props = JsonUtils.match_rules_update_properties(config.rules, stream_props)
        if Settings.get_boolean('node.stream.restore-props') and stream_props['state.restore-props'] ~= 'false' then
            local key = formKey(stream_props)
            if not key then
                return
            end
            local stored_values = getStoredStreamProps(key) or {}
            local hasChanges = false
            log:info(node, 'saving stream props for ' .. tostring(stream_props['node.name']))
            for p in node:iterate_params('Props') do
                local props = cutils.parseParam(p, 'Props')
                if not props then
                    goto skip_prop
                end
                if props.volume ~= stored_values.volume then
                    stored_values.volume = props.volume
                    hasChanges = true
                end
                if props.mute ~= stored_values.mute then
                    stored_values.mute = props.mute
                    hasChanges = true
                end
                if props.channelVolumes then
                    stored_values.channelVolumes = props.channelVolumes
                    hasChanges = true
                end
                if props.channelMap then
                    stored_values.channelMap = props.channelMap
                    hasChanges = true
                end
                ::skip_prop::
            end
            if hasChanges then
                saveStreamProps(key, stored_values)
            end
        end
    end,
})
store_stream_target_hook = SimpleEventHook({ --- save "target.node"/"target.object" on metadata changes
    name = 'node/store-stream-target-metadata-changed',
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
        local nodes_om = source:call('get-object-manager', 'node')
        local props = event:get_properties()
        local subject_id = props['event.subject.id']
        local target_key = props['event.subject.key']
        local target_value = props['event.subject.value']
        local node = nodes_om:lookup({
            Constraint({
                'bound-id',
                '=',
                subject_id,
                type = 'gobject',
            }),
        })
        if not node then
            return
        end
        local stream_props = node.properties
        stream_props = JsonUtils.match_rules_update_properties(config.rules, stream_props)
        if stream_props['state.restore-target'] == 'false' then
            return
        end
        local key = formKey(stream_props)
        if not key then
            return
        end
        local target_name = nil
        if target_value and target_value ~= '-1' then
            local target_node
            if target_key == 'target.object' then
                target_node = nodes_om:lookup({
                    Constraint({
                        'object.serial',
                        '=',
                        target_value,
                        type = 'pw-global',
                    }),
                })
            else
                target_node = nodes_om:lookup({
                    Constraint({
                        'bound-id',
                        '=',
                        target_value,
                        type = 'gobject',
                    }),
                })
            end
            if target_node then
                target_name = target_node.properties['node.name']
            end
        end
        log:info(
            node,
            'saving stream target for ' .. tostring(stream_props['node.name']) .. ' -> ' .. tostring(target_name)
        )
        local stored_values = getStoredStreamProps(key) or {}
        stored_values.target = target_name
        saveStreamProps(key, stored_values)
    end,
})
--- populate route-settings metadata
function populateMetadata(metadata) ---@param metadata any
    local key = 'Output/Audio:media.role:Notification' --- copy state into the metadata
    local p = getStoredStreamProps(key)
    if p then
        p.channels = p.channelMap and Json.Array(p.channelMap)
        p.volumes = p.channelVolumes and Json.Array(p.channelVolumes)
        p.channelMap = nil
        p.channelVolumes = nil
        p.target = nil
        key = string.gsub(key, ':', '.', 1) -- pipewire-pulse expects the key to be
        metadata:set(0, 'restore.stream.' .. key, 'Spa:String:JSON', Json.Object(p):to_string()) --- "restore.stream.Output/Audio.media.role:Notification"
    end
end

route_settings_metadata_changed_hook = SimpleEventHook({ --- track route-settings metadata changes
    name = 'node/route-settings-metadata-changed',
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
                'route-settings',
            }),
            Constraint({
                'event.subject.key',
                '=',
                'restore.stream.Output/Audio.media.role:Notification',
            }),
            Constraint({
                'event.subject.spa_type',
                '=',
                'Spa:String:JSON',
            }),
            Constraint({
                'event.subject.value',
                'is-present',
            }),
        }),
    },
    execute = function(event)
        local props = event:get_properties()
        local subject_id = props['event.subject.id']
        local key = props['event.subject.key']
        local value = props['event.subject.value']
        local json = Json.Raw(value)
        if json == nil or not json:is_object() then
            return
        end
        local vparsed = json:parse()
        key = string.sub(key, string.len('restore.stream.') + 1)
        key = string.gsub(key, '%.', ':', 1)
        log:debug('route-settings update for subject ', subject_id, ', key ', key)
        local stored_values = getStoredStreamProps(key) or {}
        if vparsed.volume ~= nil then
            stored_values.volume = vparsed.volume
        end
        if vparsed.mute ~= nil then
            stored_values.mute = vparsed.mute
        end
        if vparsed.channels ~= nil then
            stored_values.channelMap = vparsed.channels
        end
        if vparsed.volumes ~= nil then
            stored_values.channelVolumes = vparsed.volumes
        end
        saveStreamProps(key, stored_values)
    end,
})
---@param node any
---@return number[] volumes
function buildDefaultChannelVolumes(node) ---@cast node WPNode
    local node_props = node.properties
    local direction = cutils.mediaClassToDirection(node_props['media.class'] or '')
    local def_vol = 1.0 ---@type number
    local channels = 2
    local res = {}
    local str = node.properties['state.default-volume']
    if str ~= nil then
        local n = tonumber(str)
        if n ~= nil then
            def_vol = n
        end
    elseif direction == 'input' then
        def_vol = Settings.get_float('node.stream.default-capture-volume')
    elseif direction == 'output' then
        def_vol = Settings.get_float('node.stream.default-playback-volume')
    end
    for pod in node:iterate_params('Format') do
        local pod_parsed = pod:parse()
        if pod_parsed ~= nil then
            channels = pod_parsed.properties.channels
            break
        end
    end
    log:info(node, 'using default volume: ' .. tostring(def_vol) .. ', channels: ' .. tostring(channels))
    while #res < channels do
        table.insert(res, def_vol)
    end
    return res
end

---@return table<string, any>|nil props
function getStoredStreamProps(key) ---@param key string
    local value = state_table[key]
    if not value then
        return nil
    end
    local json = Json.Raw(value)
    if not json or not json:is_object() then
        return nil
    end
    return json:parse()
end

---@param p table<string, any>
function saveStreamProps(key, p) ---@param key string
    assert(type(p) == 'table')

    p.channelMap = p.channelMap and Json.Array(p.channelMap)
    p.channelVolumes = p.channelVolumes and Json.Array(p.channelVolumes)

    state_table[key] = Json.Object(p):to_string()
    state:save_after_timeout(state_table)
end

---@return string|nil key
function formKey(properties) ---@param properties table<string, any>
    local keys = {
        'media.role',
        'application.id',
        'application.name',
        'media.name',
        'node.name',
    }
    local key_base = nil
    for _, k in ipairs(keys) do
        local p = properties[k]
        if p then
            key_base = string.format('%s:%s:%s', properties['media.class']:gsub('^Stream/', ''), k, p)
            break
        end
    end
    return key_base
end

function toggleState(enable) ---@param enable boolean
    if enable and not state then
        state = State('stream-properties')
        state_table = state:load()
        restore_stream_hook:register()
        store_stream_props_hook:register()
        store_stream_target_hook:register()
        route_settings_metadata_changed_hook:register()
        rs_metadata = ImplMetadata('route-settings')
        rs_metadata:activate(Features.ALL, function(m, e)
            if e then
                log:warning('failed to activate route-settings metadata: ' .. tostring(e))
            else
                populateMetadata(m)
            end
        end)
    elseif not enable and state then
        state = nil
        state_table = nil
        restore_stream_hook:remove()
        store_stream_props_hook:remove()
        store_stream_target_hook:remove()
        route_settings_metadata_changed_hook:remove()
        rs_metadata = nil
    end
end

Settings.subscribe('node.stream.restore-props', function()
    toggleState(Settings.get_boolean('node.stream.restore-props') or Settings.get_boolean('node.stream.restore-target'))
end)
Settings.subscribe('node.stream.restore-target', function()
    toggleState(Settings.get_boolean('node.stream.restore-props') or Settings.get_boolean('node.stream.restore-target'))
end)
toggleState(Settings.get_boolean('node.stream.restore-props') or Settings.get_boolean('node.stream.restore-target'))
