-- /qompassai/dotfiles/.config/wireplumber/scripts/node/software-dsp.lua
-- Qompass AI WirePlumber Node Software- Digital Signal Processing(DSP) Script
-- Copyright (C) 2026 Qompass AI, All rights reserved
------------------------------------------------------------------------------
log = Log.open_topic('s-node')
config = { ---@type WPDSPConfig
    rules = Conf.get_section_as_json('node.filter-graph.rules', Json.Array({})), ---@type WPJsonObject
}
filter_nodes = {} ---@type WPFilterNodes
hidden_nodes = {} ---@type WPHiddenNodes
---@param client WPClient
local function apply_hidden_nodes_to_client(client)
    for id, _ in pairs(hidden_nodes) do
        if not client.properties['wireplumber.daemon'] then
            client:update_permissions({
                [id] = '-',
            })
        end
    end
end
SimpleEventHook({
    name = 'node/dsp/create-dsp-node',
    interests = {
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'node-added',
            }),
        }),
    },
    execute = function(event) ---@param event WPNodeEvent
        local node = event:get_subject()
        JsonUtils.match_rules(
            config.rules,
            node.properties, ---@type WPProperties
            function(action, value)
                if action ~= 'create-filter' then
                    return
                end
                local props = value:parse() ---@type WPDspRuleProps
                log:debug('DSP rule found for ' .. node.properties['node.name'])
                if props['filter-graph'] then
                    log:debug('Loading filter graph for ' .. node.properties['node.name'])
                    filter_nodes[node.id] = LocalModule('libpipewire-module-filter-chain', props['filter-graph'], {})
                elseif props['filter-path'] then
                    log:debug('Loading filter graph for ' .. node.properties['node.name'] .. ' from disk')
                    local conf = Conf(props['filter-path'], {
                        ['as-section'] = 'node.software-dsp.graph',
                        ['no-fragments'] = true,
                    })
                    local err = conf:open()
                    if not err then
                        local args = conf:get_section_as_json('node.software-dsp.graph'):to_string()
                        filter_nodes[node.id] = LocalModule('libpipewire-module-filter-chain', args, {})
                    else
                        log:warning('Unable to load filter graph for ' .. node.properties['node.name'])
                    end
                end
                if props['hide-parent'] then
                    log:debug('Setting permissions to \'-\' on ' .. node.properties['node.name'] .. ' for open clients')
                    local client_om = ObjectManager({
                        Interest({ type = 'client' }),
                    })
                    client_om:connect(
                        'object-added',
                        ---@param om WPObjectManager
                        ---@param client WPClient
                        function(om, client)
                            log:debug('client-added via ObjectManager: ', om)
                            apply_hidden_nodes_to_client(client)
                        end,
                        nil
                    )
                    client_om:activate()
                    hidden_nodes[node['bound-id']] = node.id
                end
            end
        )
    end,
}):register()
SimpleEventHook({
    name = 'node/dsp/free-dsp-node',
    interests = {
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'node-removed',
            }),
        }),
    },
    execute = function(event) ---@param event WPNodeEvent
        local node = event:get_subject() ---@type WPNode
        if filter_nodes[node.id] then
            log:debug('Freeing filter on node ' .. node.id)
            filter_nodes[node.id] = nil
            hidden_nodes[node['bound-id']] = nil
        end
    end,
}):register()
SimpleEventHook({
    name = 'client/apply-hidden-nodes',
    interests = {
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'client-added',
            }),
        }),
    },
    execute = function(event)
        local client = event:get_subject() ---@cast client WPClient
        apply_hidden_nodes_to_client(client)
    end,
}):register()
