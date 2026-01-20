on_demand_objects = {}
object_constructors = {
    ['pw-module'] = LocalModule,
    ['metadata'] = function(name, args)
        local m = ImplMetadata(name, args)
        m:activate(Features.ALL, function(m, e)
            if e then
                Log.warning('failed to activate on-demand metadata `' .. name .. '`: ' .. tostring(e))
            end
        end)
        return m
    end,
}
function handle_metadata_changed(m, subject, key, type, value)
    -- destroy all objects when metadata is cleared
    if not key then
        on_demand_objects = {}
        return
    end
    local object_id = key .. '@' .. tostring(subject)
    if on_demand_objects[object_id] then -- destroy existing object instance, if needed
        Log.debug('destroy on-demand object: ' .. object_id)
        on_demand_objects[object_id] = nil
    end

    if value then
        local json = Json.Raw(value)
        if not json:is_object() then
            Log.warning('loading \'' .. object_id .. '\' failed: expected JSON object, got: \'' .. value .. '\'')
            return
        end
        local obj = json:parse(1)
        if not obj.type then
            Log.warning('loading \'' .. object_id .. '\' failed: no object type specified')
            return
        end
        if not obj.name then
            Log.warning('loading \'' .. object_id .. '\' failed: no object name specified')
            return
        end
        local constructor = object_constructors[obj.type]
        if not constructor then
            Log.warning('loading \'' .. object_id .. '\' failed: unknown object type: ' .. obj.type)
            return
        end

        Log.info('load on-demand object: ' .. object_id .. ' -> ' .. obj.name)
        on_demand_objects[object_id] = constructor(obj.name, obj.args)
    end
end
objects_metadata = ImplMetadata('sm-objects')
objects_metadata:activate(Features.ALL, function(m, e)
    if e then
        Log.warning('failed to activate the sm-objects metadata: ' .. tostring(e))
    else
        m:connect('changed', handle_metadata_changed)
    end
end)
