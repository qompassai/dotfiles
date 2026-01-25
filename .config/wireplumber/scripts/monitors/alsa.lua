-- /qompassai/dotfiles/.config/wireplumber/scripts/monitors/alsa.lua
-- Qompass AI WirePlumber Alsa Monitors Script
-- Copyright (C) 2026 Qompass AI, All rights reserved
------------------------------------------------------------------------
SPLIT_PCM_PARENT_OFFSET = 256 ---@type integer
SPLIT_PCM_OFFSET = 512 ---@type integer
cutils = require('common-utils') ---@type WPUtils
log = Log.open_topic('s-monitors') ---@type WPLog
config = {}
config.reserve_device = Core.test_feature('monitor.alsa.reserve-device')
config.properties = Conf.get_section_as_properties('monitor.alsa.properties')
config.rules = Conf.get_section_as_json('monitor.alsa.rules', Json.Array({}))
device_names_table = {} ---@type table<string, boolean>
node_names_table = {} ---@type table<string, boolean>
id_name_table = {} ---@type table<number, table<number, string>>
---@return string|nil
function nonempty(str) ---@param str string
    return str ~= '' and str or nil
end

---@return nil
function applyDefaultDeviceProperties(properties) ---@param properties WPProperties
    properties['api.alsa.use-acp'] = true
    properties['api.acp.auto-profile'] = false
    properties['api.acp.auto-port'] = false
    properties['api.dbus.ReserveDevice1.Priority'] = -20
    properties['api.alsa.split-enable'] = true
end

---@param properties WPProperties
---@return WPNode|nil
function createSplitPCMHWNode(dev_props, properties) ---@param dev_props WPProperties
    local skip_keys = {
        'api.alsa.split.position',
        'card.profile.device',
        'device.profile.description',
        'device.profile.name',
    }
    local props = {}
    for k, v in pairs(properties) do
        props[k] = v
    end
    for _, k in pairs(skip_keys) do
        props[k] = nil
    end
    props['node.name'] = props['api.alsa.split.name'] --- create the underlying hidden ALSA node
    props['node.description'] =
        string.format('%s %s', dev_props['device.description'], props['api.alsa.path']:gsub('^[^,]*[,:]', ''))
    if props['api.alsa.pcm.stream'] == 'capture' then
        props['media.class'] = 'Audio/Source/Internal'
    else
        props['media.class'] = 'Audio/Sink/Internal'
    end
    props['api.alsa.use-chmap'] = false
    props['api.alsa.split.parent'] = true
    props['audio.position'] = props['api.alsa.split.hw-position']
    local channels = Json.Raw(props['api.alsa.split.hw-position']):parse()
    props['audio.channels'] = tostring(#channels)
    props = JsonUtils.match_rules_update_properties(config.rules, props)
    if cutils.parseBool(props['node.disabled']) then
        log:notice('ALSA node ' .. props['node.name'] .. ' disabled')
        return nil
    end
    return Node('adapter', props)
end

---@param parent WPObject
---@param id number
---@param obj_type string
---@param factory string
---@param properties WPProperties
---@return WPLocalModule
function createSplitPCMLoopback(parent, id, obj_type, factory, properties)
    local skip_keys = { --- not suitable for loopback
        'audio.rate',
        'clock.quantum-limit',
        'factory.name',
        'node.driver',
        'node.pause-on-idle',
        'node.want-driver',
        'port.group',
        'priority.driver',
        'resample.disable',
        'resample.prefill',
    }
    local args
    local props = {}
    props['node.virtual'] = false
    for k, v in pairs(properties) do
        props[k] = v
    end
    for _, k in pairs(skip_keys) do
        props[k] = nil
    end
    local split_props = {
        ['node.name'] = properties['node.name'] .. '.split',
        ['node.description'] = string.format(I18n.gettext('Split %s'), properties['node.description']),
        ['audio.position'] = properties['api.alsa.split.position'],
        ['stream.dont-remix'] = true,
        ['node.passive'] = true,
        ['node.dont-fallback'] = true,
        ['node.linger'] = true,
        ['state.restore-props'] = false,
        ['target.object'] = properties['api.alsa.split.name'],
    }
    if properties['api.alsa.pcm.stream'] == 'playback' then
        props['media.class'] = 'Audio/Sink'
        split_props['media.class'] = 'Stream/Output/Audio/Internal'
        args = Json.Object({
            ['capture.props'] = Json.Object(props),
            ['playback.props'] = Json.Object(split_props),
        })
    else
        props['media.class'] = 'Audio/Source'
        split_props['media.class'] = 'Stream/Input/Audio/Internal'
        args = Json.Object({
            ['playback.props'] = Json.Object(props),
            ['capture.props'] = Json.Object(split_props),
        })
    end
    return LocalModule('libpipewire-module-loopback', args:get_data(), {})
end

devices_om = ObjectManager({
    Interest({
        type = 'device',
    }),
})
split_nodes_om = ObjectManager({
    Interest({
        type = 'node',
        Constraint({
            'api.alsa.split.position',
            '+',
            type = 'pw',
        }),
    }),
})
split_nodes_om:connect('object-added', function(_, node)
    if not monitor then --- Connect ObjectConfig events to the right node
        return
    end
    local interest = Interest({
        type = 'device',
        Constraint({
            'object.id',
            '=',
            node.properties['device.id'],
        }),
    })
    log:info('Split PCM node found: ' .. tostring(node['bound-id']))
    for device in devices_om:iterate(interest) do
        local device_id = device.properties['spa.object.id']
        if not device_id then
            goto next_device
        end
        local spa_device = monitor:get_managed_object(tonumber(device_id))
        if not spa_device then
            goto next_device
        end
        ---@cast spa_device WPSpaDevice
        local id = node.properties['card.profile.device'] ---@type string|number|nil
        if id ~= nil then
            local card_id = tonumber(id) ---@type number|nil
            if card_id ~= nil then
                ---@cast card_id number
                log:info('.. assign to device: ' .. tostring(device['bound-id']) .. ' node ' .. tostring(card_id))
                spa_device:store_managed_object(card_id, node)
            end
        end

        ::next_device::
    end
end)
---@param parent WPSpaDevice
---@param id number
---@param obj_type string
---@param factory string
---@param properties WPProperties
---@return nil
function createNode(parent, id, obj_type, factory, properties)
    local dev_props = parent.properties
    local parent_id = tonumber(dev_props['spa.object.id'])
    properties['device.id'] = parent['bound-id']    --- set the device id and spa factory name; REQUIRED, do not change
    properties['factory.name'] = factory
    properties['node.pause-on-idle'] = false        --- set the default pause-on-idle setting
    if dev_props['api.alsa.use-acp'] ~= 'true' then --- try to negotiate the max amount of channels
        properties['audio.channels'] = properties['audio.channels'] or '64'
    end

    local dev = properties['api.alsa.pcm.device'] or properties['alsa.device'] or '0'
    local subdev = properties['api.alsa.pcm.subdevice'] or properties['alsa.subdevice'] or '0'
    local stream = properties['api.alsa.pcm.stream'] or 'unknown'
    local profile = properties['device.profile.name'] or (stream .. '.' .. dev .. '.' .. subdev)
    local profile_desc = properties['device.profile.description']
    if not properties['priority.driver'] then
        local priority = (dev == '0') and 1000 or 744
        if stream == 'capture' then
            priority = priority + 1000
        end
        priority = priority - (tonumber(dev) * 16) - tonumber(subdev)
        if profile:find('^pro%-') then
            priority = priority + 500
        elseif profile:find('^analog%-') then
            priority = priority + 9
        elseif profile:find('^iec958%-') then
            priority = priority + 8
        end

        if dev_props['device.bus'] == 'usb' then
            priority = priority + 100
        end
        properties['priority.driver'] = priority
        properties['priority.session'] = priority
    end

    if not properties['media.class'] then --- ensure the node has a media class
        if stream == 'capture' then
            properties['media.class'] = 'Audio/Source'
        else
            properties['media.class'] = 'Audio/Sink'
        end
    end
    -- ensure the node has a name
    if not properties['node.name'] then
        local name = (stream == 'capture' and 'alsa_input' or 'alsa_output')
            .. '.'
            .. (dev_props['device.name']:gsub('^alsa_card%.(.+)', '%1') or dev_props['device.name'] or 'unnamed-device')
            .. '.'
            .. profile
        -- sanitize name
        name = name:gsub('([^%w_%-%.])', '_')
        properties['node.name'] = name
        log:info('Creating node ' .. name)

        -- deduplicate nodes with the same name
        for counter = 2, 99, 1 do
            if node_names_table[properties['node.name']] ~= true then
                break
            end
            properties['node.name'] = name .. '.' .. counter
            log:info('deduplicating node name -> ' .. properties['node.name'])
        end
    else
        log:info('Creating node ' .. properties['node.name'])
    end
    local nick_val = nonempty(properties['node.nick']) ---@type string|nil
        or nonempty(properties['api.alsa.pcm.name'])
        or nonempty(properties['alsa.name'])
        or nonempty(profile_desc)
        or dev_props['device.nick'] ---@type string|nil

    local nick = nick_val or '' ---@type string
    if nick == 'USB Audio' then
        nick = dev_props['device.nick'] or nick
    end
    -- also sanitize nick, replace ':' with ' '
    properties['node.nick'] = nick:gsub('(:)', ' ')
    if not properties['node.description'] then --- ensure the node has a description
        local desc = nonempty(dev_props['device.description']) or 'unknown'
        local name = nonempty(properties['api.alsa.pcm.name']) or nonempty(properties['api.alsa.pcm.id']) or dev
        if profile_desc then
            desc = desc .. ' ' .. profile_desc
        elseif subdev ~= '0' then
            desc = desc .. ' (' .. name .. ' ' .. subdev .. ')'
        elseif dev ~= '0' then
            desc = desc .. ' (' .. name .. ')'
        end

        -- also sanitize description, replace ':' with ' '
        properties['node.description'] = desc:gsub('(:)', ' ')
    end

    -- add api.alsa.card.* and alsa.* properties for rule matching purposes
    for k, v in pairs(dev_props) do
        if k:find('^api%.alsa%.card%..*') or k:find('^alsa%..*') then
            properties[k] = v
        end
    end
    ---@return string|nil
    local function nonempty(s) ---@param s string|nil
        if s == nil or s == '' then
            return nil
        end
        return s
    end
    local vm_type = Core.get_vm_type() ---@type string|nil
    local vm_name = nonempty(vm_type) ---@type string|nil
    if vm_name ~= nil then
        -- inside this block vm_name is `string`
        properties['cpu.vm.name'] = vm_name
    end

    local orig_properties = {} --- apply properties from rules defined in JSON .conf file
    for k, v in pairs(properties) do
        orig_properties[k] = v
    end
    properties = JsonUtils.match_rules_update_properties(config.rules, properties)

    if cutils.parseBool(properties['node.disabled']) then
        log:notice('ALSA node ' .. properties['node.name'] .. ' disabled')
        return
    end
    node_names_table[properties['node.name']] = true
    id_name_table[parent_id][id] = properties['node.name']
    if properties['api.alsa.split.position'] ~= nil then -- handle split HW node
        local split_hw_node_name = string.format(
            '%s.%s',
            (stream == 'capture' and 'alsa_input' or 'alsa_output'),
            properties['api.alsa.path']:gsub('([:,])', '_')
        )
        properties['api.alsa.split.name'] = split_hw_node_name
        orig_properties['api.alsa.split.name'] = split_hw_node_name
        if not node_names_table[split_hw_node_name] then
            log:info('Create ALSA SplitPCM HW node ' .. split_hw_node_name)
            local node = createSplitPCMHWNode(dev_props, orig_properties)
            if node ~= nil then
                node:activate(Feature.Proxy.BOUND)
                parent:store_managed_object(SPLIT_PCM_PARENT_OFFSET + id, node)
                node_names_table[split_hw_node_name] = true
                id_name_table[parent_id][SPLIT_PCM_PARENT_OFFSET + id] = split_hw_node_name
            end
        end

        log:info('Create ALSA SplitPCM split node ' .. properties['node.name']) --- create split PCM node
        local loopback = createSplitPCMLoopback(parent, id, obj_type, factory, properties)
        parent:store_managed_object(SPLIT_PCM_OFFSET + id, loopback)
        parent:set_managed_pending(id)
        return
    end
    local node = Node('adapter', properties) --- create the node
    parent:set_managed_pending(id)
    node:activate(Feature.Proxy.BOUND, function(_, err)
        if err then
            log:warning('Failed to create ' .. properties['node.name'] .. ': ' .. tostring(err))
        end
        parent:store_managed_object(id, node)
    end)
end

---@param parent WPSpaDevice
---@param id number
---@return nil
function removeNode(parent, id)
    local parent_id = tonumber(parent.properties['spa.object.id'])
    local ids = { id, SPLIT_PCM_PARENT_OFFSET + id, SPLIT_PCM_OFFSET + id }
    for _, j in pairs(ids) do
        local node_name = id_name_table[parent_id][j]
        parent:store_managed_object(j, nil)
        if node_name ~= nil then
            log:info('Removing node ' .. node_name)
            node_names_table[node_name] = nil
            id_name_table[parent_id][j] = nil
        end
    end
end

---@param parent WPSpaDevice
---@param id number
---@param factory string
---@param properties WPProperties
---@return nil
function createDevice(parent, id, factory, properties)
    id_name_table[id] = {}
    properties['spa.object.id'] = id
    local device = SpaDevice(factory, properties)
    if device then
        device:connect('create-object', createNode)
        device:connect('object-removed', removeNode)
        device:activate(Feature.SpaDevice.ENABLED + Feature.Proxy.BOUND)
        parent:store_managed_object(id, device)
    else
        log:warning('Failed to create "' .. factory .. '" device')
    end
end

--- Release all nodes associated with a given ALSA device id
--- and recycle its name for future devices.
---@param parent WPSpaDevice The parent SPA device that owns the nodes
---@param id number The PipeWire device id to remove
---@return nil
function removeDevice(parent, id)
    if id_name_table[id] ~= nil then
        log:info(string.format('Removing device id=%d from parent=%s', id, tostring(parent and parent.id or 'unknown')))
        for _, node_name in pairs(id_name_table[id]) do
            log:info('Release ' .. node_name)
            node_names_table[node_name] = nil
        end
        id_name_table[id] = nil
    else
        log:debug(
            string.format(
                'removeDevice: no entries for id=%d on parent=%s',
                id,
                tostring(parent and parent.id or 'unknown')
            )
        )
    end
end

---@param parent WPSpaDevice
---@param id number
---@param obj_type string
---@param factory string
---@param properties WPProperties
---@return nil
function prepareDevice(parent, id, obj_type, factory, properties)
    log:debug( -- log basic context so parent/obj_type/factory are actually used
        string.format(
            'prepareDevice: parent=%s id=%d obj_type=%s factory=%s',
            tostring(parent and parent.id or 'unknown'),
            id,
            obj_type,
            factory
        )
    )
    local name = 'alsa_card.' --- ensure the device has an appropriate name
        .. (properties['device.name'] or properties['device.bus-id'] or properties['device.bus-path'] or tostring(id))
        :gsub(
            '([^%w_%-%.])',
            '_'
        )
    properties['device.name'] = name
    for counter = 2, 99, 1 do
        if device_names_table[properties['device.name']] ~= true then
            device_names_table[properties['device.name']] = true
            break
        end
        properties['device.name'] = name .. '.' .. counter
    end
    if not properties['device.description'] then
        local d = nil
        local f = properties['device.form-factor']
        local c = properties['device.class']
        local n = properties['api.alsa.card.name']
        if n == 'Loopback' then
            d = I18n.gettext('Loopback')
        elseif f == 'internal' then
            d = I18n.gettext('Built-in Audio')
        elseif c == 'modem' then
            d = I18n.gettext('Modem')
        end
        d = d
            or properties['device.product.name']
            or properties['api.alsa.card.name']
            or properties['alsa.card_name']
            or 'Unknown device'
        properties['device.description'] = d
    end
    properties['device.nick'] = properties['device.nick']
        or properties['api.alsa.card.name']
        or properties['alsa.card_name']
    if not properties['device.icon-name'] then
        local icon_map = {
            ['microphone'] = 'audio-input-microphone',
            ['webcam'] = 'camera-web',
            ['handset'] = 'phone',
            ['portable'] = 'multimedia-player',
            ['tv'] = 'video-display',
            ['headset'] = 'audio-headset',
            ['headphone'] = 'audio-headphones',
            ['speaker'] = 'audio-speakers',
            ['hands-free'] = 'audio-handsfree',
        }
        local f = properties['device.form-factor']
        local c = properties['device.class']
        local b = properties['device.bus']
        local icon = icon_map[f] or ((c == 'modem') and 'modem') or 'audio-card'
        properties['device.icon-name'] = icon .. '-analog' .. (b and ('-' .. b) or '')
    end
    applyDefaultDeviceProperties(properties)
    properties = JsonUtils.match_rules_update_properties(config.rules, properties)
    if cutils.parseBool(properties['device.disabled']) then
        log:notice('ALSA card/device ' .. properties['device.name'] .. ' disabled')
        device_names_table[properties['device.name']] = nil
        return
    end
    if cutils.parseBool(properties['api.alsa.use-acp']) then
        log:info('Enabling the use of ACP on ' .. properties['device.name'])
        factory = 'api.alsa.acp.device'
    end
    if Settings.get_boolean('monitor.alsa.autodetect-hdmi-channels') then
        properties['api.acp.use-eld-channels'] = true
    end
    if rd_plugin and properties['api.alsa.card'] then
        local rd_name = 'Audio' .. properties['api.alsa.card']
        local rd = rd_plugin:call(
            'create-reservation',
            rd_name,
            cutils.get_application_name(),
            properties['device.name'],
            properties['api.dbus.ReserveDevice1.Priority']
        )
        properties['api.dbus.ReserveDevice1'] = rd_name
        rd:connect('notify::state', function(reservation, _pspec)
            local state = reservation['state']
            if state == 'acquired' then
                createDevice(parent, id, factory, properties)
            elseif state == 'available' then
                reservation:call('acquire')
            elseif state == 'busy' then
                removeDevice(parent, id)
                parent:store_managed_object(id, nil)
            end
        end)
        rd:connect('release-requested', function(reservation)
            log:info('release requested')
            parent:store_managed_object(id, nil)
            reservation:call('release')
        end)
        rd:call('acquire')
    else
        createDevice(parent, id, factory, properties)
    end
end

---@return WPSpaDevice|nil
function createMonitor()
    local m = SpaDevice('api.alsa.enum.udev', config.properties)
    if m == nil then
        log:notice('PipeWire\'s ALSA SPA plugin is missing or broken. ' .. 'Sound cards will not be supported')
        return nil
    end
    m:connect('create-object', prepareDevice)
    m:connect('object-removed', function(parent, id)
        removeDevice(parent, id)
        local device = parent:get_managed_object(id)
        if not device then
            return
        end

        if rd_plugin then
            local rd_name = device.properties['api.dbus.ReserveDevice1']
            if rd_name then
                rd_plugin:call('destroy-reservation', rd_name)
            end
        end
        device_names_table[device.properties['device.name']] = nil
    end)
    device_names_table = {} --- reset the name tables to make sure names are recycled
    node_names_table = {}
    id_name_table = {}
    log:info('Activating ALSA monitor') --- activate monitor
    m:activate(Feature.SpaDevice.ENABLED)
    return m
end

if config.reserve_device then
    rd_plugin = Plugin.find('reserve-device')
end
if rd_plugin and rd_plugin:call('get-dbus')['state'] ~= 'connected' then
    log:notice('reserve-device plugin is not connected to D-Bus, ' .. 'disabling device reservation')
    rd_plugin = nil
end
if rd_plugin then
    local dbus = rd_plugin:call('get-dbus')
    dbus:connect('notify::state', function(b, pspec)
        local prop_name = pspec and pspec['name'] or 'state' -- pspec is a GParamSpec describing which property changed
        local state = b['state']
        log:info(string.format('rd-plugin property "%s" changed, state=%s', prop_name, tostring(state)))
        if state == 'connected' then
            log:info('Creating ALSA monitor')
            monitor = createMonitor()
        elseif state == 'closed' then
            log:info('Destroying ALSA monitor')
            monitor = nil
        end
    end)
end
monitor = createMonitor() --- create the monitor
devices_om:activate()
split_nodes_om:activate()
