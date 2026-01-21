-- /qompassai/dotfiles/.config/wireplumber/scripts/node/find-media-role-default-volume.lua
-- Qompass AI WirePlumber Node Find Media Role  Default Volume Script
-- Copyright (C) 2026 Qompass AI, All rights reserved
-----------------------------------------------------------------------------------------
log = Log.open_topic('s-node') ---@type WPLog
local cutils = require('common-utils') ---@type WPUtils
---@return nil
function findHighestPriorityRoleNode(node_om) ---@param node_om WPObjectManager
    local best_role = nil ---@type string|nil
    local best_prio = 0 ---@type number
    local default_role = Settings.get('node.stream.default-media-role') ---@type WPJsonObject|nil
    if default_role then ---@cast default_role WPJsonObject
        default_role = default_role:parse() ---@type WPJsonObject|nil
    end
    for ni in
        node_om:iterate({
            type = 'node',
            Constraint({
                'media.class',
                '=',
                'Audio/Sink',
            }),
            Constraint({
                'node.name',
                '#',
                'input.loopback.sink.role.*',
            }),
        })
    do ---@cast ni WPNode
        local ni_props = ni.properties
        local roles = ni_props['device.intended-roles'] ---@type string|nil
        local node_name = ni_props['node.name'] ---@type string
        local prio = tonumber(ni_props['policy.role-based.priority'])
        if best_role == nil and roles and default_role then
            local roles_table = Json.Raw(roles):parse() ---@type string[]
            for _, v in ipairs(roles_table) do
                if default_role == v and prio ~= nil then
                    best_role = node_name
                    best_prio = prio
                    break
                end
            end
        end
        if ni.state == 'running' and prio ~= nil and prio > best_prio then
            best_role = node_name
            best_prio = prio
        end
    end
    log:info(string.format('Volume control is on : \'%s\', prio %d', best_role, best_prio))
    local metadata = cutils.get_default_metadata_object()
    metadata:set(
        0,
        'current.role-based.volume.control',
        'Spa:String:JSON',
        Json.Object({
            ['name'] = best_role,
        }):to_string()
    )
end

SimpleEventHook({
    name = 'node/rescan-for-media-role-volume',
    interests = {
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'rescan-for-media-role-volume',
            }),
        }),
    },
    execute = function(event)
        local source = event:get_source()
        local node_om = source:call('get-object-manager', 'node')
        findHighestPriorityRoleNode(node_om)
    end,
}):register()

SimpleEventHook({ --- Track best volume control for media role based priorities
    name = 'node/find-media-role-default-volume',
    interests = {
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'node-added',
            }),
            Constraint({
                'media.class',
                '=',
                'Audio/Sink',
            }),
            Constraint({
                'node.name',
                '#',
                'input.loopback.sink.role.*',
            }),
        }),
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'node-state-changed',
            }),
            Constraint({
                'media.class',
                '=',
                'Audio/Sink',
            }),
            Constraint({
                'node.name',
                '#',
                'input.loopback.sink.role.*',
            }),
        }),
    },
    execute = function(event)
        local source = event:get_source()
        local node_om = source:call('get-object-manager', 'node')
        findHighestPriorityRoleNode(node_om)
        source:call('schedule-rescan', 'media-role-volume')
    end,
}):register()
