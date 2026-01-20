agutils = require('audio-group-utils')
PW_AUDIO_NAMESPACE = 'pw-audio-namespace'
node_directions = {}
group_loopback_modules = {}
group_loopback_modules['input'] = {}
group_loopback_modules['output'] = {}
---@param id integer
---@param props WPProperties
---@return '"input"'|'"output"'|nil
function GetNodeDirection(id, props)
    if string.find(props['media.class'], 'Stream/Input/Audio') then
        return 'input'
    elseif string.find(props['media.class'], 'Stream/Output/Audio') then
        return 'output'
    end
    return nil
end

---@return string|nil group
---@return string|nil target_object
function GetNodeAudioGroup(pid) ---@param pid number
    local group = nil
    local target_object = nil
    local curr_pid = pid --- We group a processes by PW_AUDIO_NAMESPACE.<pid> ancestor
    while curr_pid ~= 0 do ---@cast curr_pid integer
        local pid_info = ProcUtils.get_proc_info(curr_pid)
        local arg0 = pid_info:get_arg(0)

        if
            arg0 ~= nil
            and string.find(
                arg0, --- Check if ancestor process name is PW_AUDIO_NAMESPACE
                PW_AUDIO_NAMESPACE,
                1,
                true
            )
        then
            for i = 0, pid_info:get_n_args() - 1, 1 do --- Check if the PW_AUDIO_NAMESPACE has a defined target
                local argn = pid_info:get_arg(i)
                if argn == '--' then --- Ignore any args after '--'
                    break
                end
                if (argn == '--target-object') or (argn == '-t') then --- Get target node id value if any
                    target_object = pid_info:get_arg(i + 1)
                    break
                end
            end

            group = PW_AUDIO_NAMESPACE .. '.' .. tostring(curr_pid) --- We name the audio group as PW_AUDIO_NAMESPACE.<pid>
            break
        end
        curr_pid = pid_info:get_parent_pid()
    end
    return group, target_object
end

---@param props WPProperties
---@param group string
---@param target_object string|nil
---@param direction '"input"'|'"output"'
---@return WPLocalModule
function CreateStreamLoopback(props, group, target_object, direction)
    local is_input = direction == 'input' and true or false
    local stream_props = {} -- Set stream properties
    stream_props['node.name'] = 'stream.audio_group:' .. group
    stream_props['node.description'] = 'Stream Audio Group for ' .. group
    stream_props['media.class'] = is_input and 'Stream/Input/Audio' or 'Stream/Output/Audio'
    stream_props['node.passive'] = true
    stream_props['session.audio-group'] = group
    if target_object ~= nil then
        stream_props['target.object'] = tostring(target_object)
    end
    local device_props = {} --- Set device properties
    device_props['node.name'] = 'device.audio_group:' .. group
    device_props['node.description'] = 'Device Audio Group for ' .. group
    device_props['media.class'] = is_input and 'Audio/Source' or 'Audio/Sink'
    device_props['session.audio-group'] = group
    local args = Json.Object({ --- Set loopback module args
        ['capture.props'] = Json.Object(is_input and stream_props or device_props),
        ['playback.props'] = Json.Object(is_input and device_props or stream_props),
    })
    return LocalModule('libpipewire-module-loopback', args:get_data(), {}) --- Create module
end

SimpleEventHook({
    name = 'lib/audio-group-utils/create-audio-group-loopback',
    interests = {
        EventInterest({ --- on linkable added or removed, where linkable is adapter or plain node
            Constraint({
                'event.type',
                '=',
                'node-added',
            }),
            Constraint({
                'media.class',
                '#',
                'Stream/*Audio*',
                type = 'pw-global',
            }),
            Constraint({
                'stream.monitor',
                '!',
                'true',
                type = 'pw',
            }),
            Constraint({
                'node.link-group',
                '-',
            }),
        }),
    },
    execute = function(event)
        local node = event:get_subject()
        local source = event:get_source()
        local client_om = source:call('get-object-manager', 'client')
        local id = node.id
        local bound_id = node['bound-id']
        local stream_props = node.properties
        local stream_name = stream_props['node.name']
        local client = client_om:lookup({ --- Get client
            Constraint({
                'bound-id',
                '=',
                stream_props['client.id'],
                type = 'gobject',
            }),
        })
        if client == nil then
            Log.info(node, 'Cannot get client, not grouping audio stream ' .. stream_name)
            return
        end
        local pid = tonumber(client.properties['application.process.id']) --- Get process ID
        if pid == nil then
            Log.info(node, 'Cannot get process ID, not grouping audio stream ' .. stream_name)
            return
        end
        local direction = GetNodeDirection(bound_id, stream_props) --- Get direction and add it to the table
        if direction == nil then
            Log.info(node, 'Cannot get direction, not grouping audio stream ' .. stream_name)
            return
        end
        node_directions[id] = direction
        local group, target_object = GetNodeAudioGroup(pid) --- Get group and add it to the table
        if group == nil then
            Log.info(node, 'Cannot get audio group, not grouping audio stream ' .. stream_name)
            return
        end
        agutils.set_audio_group(node, group)
        local m = group_loopback_modules[direction][group] --- Create group loopback module if it does not exist
        if m == nil then
            Log.info(
                'Creating '
                    .. direction
                    .. ' loopback for audio group '
                    .. group
                    .. (target_object and (' with target object ' .. tostring(target_object)) or '')
            )
            m = CreateStreamLoopback(stream_props, group, target_object, direction)
            group_loopback_modules[direction][group] = m
        end
    end,
}):register()
SimpleEventHook({
    name = 'lib/audio-group-utils/destroy-audio-group-loopback',
    interests = {
        EventInterest({ --- on linkable added or removed, where linkable is adapter or plain node
            Constraint({
                'event.type',
                '=',
                'node-removed',
            }),
            Constraint({
                'media.class',
                '#',
                'Stream/*Audio*',
                type = 'pw-global',
            }),
            Constraint({
                'stream.monitor',
                '!',
                'true',
                type = 'pw',
            }),
            Constraint({
                'node.link-group',
                '-',
            }),
        }),
    },
    execute = function(event)
        local node = event:get_subject()
        local id = node.id
        local direction = node_directions[id] --- Get node direction from table and remove it
        if direction == nil then
            return
        end
        node_directions[id] = nil
        local group = agutils.get_audio_group(node) --- Get node group from table and remove it
        if group == nil then
            return
        end
        agutils.set_audio_group(node, nil)
        if not agutils.contains_audio_group(group) then --- Destroy group loopback module if there are no more nodes with the same group
            Log.info('Destroying ' .. direction .. ' loopback for audio group ' .. group)
            group_loopback_modules[direction][group] = nil
        end
    end,
}):register()
