-- /qompassai/dotfiles/.config/wireplumber/scripts/node/filter-graph.lua
-- Qompass AI WirePlumber Node Filter-Graph Script
-- Copyright (C) 2026 Qompass AI, All rights reserved
------------------------------------------------------------------------
log = Log.open_topic('s-node') ---@type WPLog
config = { ---@type WPDSPConfig
    rules = Conf.get_section_as_json('node.filter-graph.rules', Json.Array({})), ---@type WPJsonObject
}
---@param graph_params any[]
---@return nil
function setNodeFilterGraphParams(node, graph_params) ---@param node WPNode
    local pod = Pod.Object({
        'Spa:Pod:Object:Param:Props',
        'Props',
        params = Pod.Struct(graph_params),
    })
    node:set_params('Props', pod)
end

SimpleEventHook({
    name = 'node/create-filter-graph',
    interests = {
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'node-added',
            }),
            Constraint({
                'library.name',
                '=',
                'audioconvert/libspa-audioconvert',
                type = 'pw',
            }),
        }),
    },
    execute = function(event) ---@param event WPEvent
        local node = event:get_subject() ---@cast node WPNode
        ---@param action string
        JsonUtils:match_rules(config.rules, node.properties, function(action, value) ---@param value WPJsonObject
            if action == 'create-filter-graph' then
                local graphs = value:parse(1) ---@type string[]
                local graph_params = {}
                for idx, val in ipairs(graphs) do
                    local index = tonumber(idx) - 1
                    local key = 'audioconvert.filter-graph.' .. tostring(index)
                    log:info(node, 'setting node filter graph param \'' .. key .. '\' to: ' .. val)
                    table.insert(graph_params, key)
                    table.insert(graph_params, val)
                end
                setNodeFilterGraphParams(node, graph_params)
            end
        end)
    end,
}):register()
