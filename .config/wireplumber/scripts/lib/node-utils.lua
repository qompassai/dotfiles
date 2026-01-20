local module = {}
function module.get_session_priority(node_props)
    local priority = node_props['priority.session']
    if not priority then -- fallback to driver priority if session priority is not set
        priority = node_props['priority.driver']
    end
    priority = tonumber(priority) or 0 --- Convert to number and clamp to integer, default 0
    return math.floor(priority)
end

return module

--[[
local module = {}
function module.get_session_priority(node_props)
    local priority = node_props['priority.session']
    if not priority then --- fallback to driver priority if session priority is not set
        priority = node_props['priority.driver']
    end
    return math.tointeger(priority) or 0
end

return module
--]]
