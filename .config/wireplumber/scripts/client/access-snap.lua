function removeClientPermissionsForOtherClients(client)
    local client_id = client.properties['pipewire.snap.id'] --- Remove access to any other clients, but allow all the process of the
    for snap_client in clients_snap:iterate() do --- same snap to access their elements
        local snap_client_id = snap_client.properties['pipewire.snap.id']
        if snap_client_id ~= client_id then
            client:update_permissions({ [snap_client['bound-id']] = '-' })
        end
    end
    for no_snap_client in clients_no_snap:iterate() do
        client:update_permissions({ [no_snap_client['bound-id']] = '-' })
    end
end

function updateClientPermissions(client)
    for node in nodes_om:iterate() do --- Remove access to Audio/Sources and Audio/Sinks based on snap permissions
        local node_id = node['bound-id']
        local property = 'pipewire.snap.audio.playback'

        if node.properties['media.class'] == 'Audio/Source' then
            property = 'pipewire.snap.audio.record'
        end

        if client.properties[property] ~= 'true' then
            client:update_permissions({ [node_id] = '-' })
        end
    end
end

clients_snap = ObjectManager({
    Interest({
        type = 'client',
        Constraint({
            'pipewire.snap.id',
            '+',
            type = 'pw',
        }),
    }),
})
clients_no_snap = ObjectManager({
    Interest({
        type = 'client',
        Constraint({
            'pipewire.snap.id',
            '-',
            type = 'pw',
        }),
    }),
})
nodes_om = ObjectManager({
    Interest({
        type = 'node',
        Constraint({
            'media.class',
            'matches',
            'Audio/*',
        }),
    }),
})
clients_snap:connect('object-added', function(om, client)
    updateClientPermissions(client) --- If a new snap client is added, adjust its permissions
    removeClientPermissionsForOtherClients(client)
end)
clients_no_snap:connect('object-added', function(om, client)
    client_id = client['bound-id'] --- If a new, non-snap client is added,
    for snap_client in clients_snap:iterate() do --- remove access to it from other snaps
        if client.properties['pipewire.snap.id'] ~= nil then
            snap_client:update_permissions({ [client_id] = '-' })
        end
    end
end)
nodes_om:connect('object-added', function(om, node)
    for client in clients_snap:iterate() do --- If a new Audio/Sink or Audio/Source node is added,
        updateClientPermissions(client) --- adjust the permissions in the snap clients
    end
end)
clients_snap:activate()
clients_no_snap:activate()
nodes_om:activate()
