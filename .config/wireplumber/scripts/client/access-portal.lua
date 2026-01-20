local bit = require("bit") --- LuaJIT bitops
MEDIA_ROLE_NONE = 0
MEDIA_ROLE_CAMERA = bit.lshift(1, 0)
log = Log.open_topic("s-client")
---@param permissions table<string, string[]>
---@param app_id string
---@param lookup string
---@return boolean
function hasPermission(permissions, app_id, lookup)
  if permissions then
    for key, values in pairs(permissions) do
      if key == app_id then
        for _, v in pairs(values) do
          if v == lookup then
            return true
          end
        end
      end
    end
  end
  return false
end

---@param media_roles_str string
---@return integer media_roles
function parseMediaRoles(media_roles_str)
  local media_roles = MEDIA_ROLE_NONE
  for role in media_roles_str:gmatch('[^,%s]+') do
    if role == "Camera" then
      media_roles = media_roles | MEDIA_ROLE_CAMERA
    end
  end
  return media_roles
end

---@param client any
---@param allow_client boolean
---@param allow_nodes boolean
function setPermissions(client, allow_client, allow_nodes)
  local client_id = client["bound-id"]
  log:info(client, "Granting ALL access to client " .. client_id)
  client:update_permissions --- Update permissions on client
  {
    [client_id] = allow_client and "all" or "-"
  }
  for node in nodes_om:iterate() do --- Update permissions on camera source nodes
    local node_id = node["bound-id"]
    client:update_permissions {
      [node_id] = allow_nodes and "all" or "-" }
  end
end

---@param client any
function updateClientPermissions(client, permissions) ---@param permissions table<string, string[]>
  local client_id = client["bound-id"]
  local str_prop = nil
  local app_id = nil
  local media_roles = nil
  local allowed = false


  str_prop = client.properties["pipewire.access.portal.is_portal"] --- Make sure the client is not the portal itself
  if str_prop == "yes" then
    log:info(client, "client is the portal itself")
    return
  end

  -- Make sure the client has a portal app Id
  str_prop = client.properties["pipewire.access.portal.app_id"]
  if str_prop == nil then
    log:info(client, "Portal managed client did not set app_id")
    return
  end
  if str_prop == "" then
    log:info(client, "Ignoring portal check for non-sandboxed client")
    setPermissions(client, true, true)
    return
  end
  app_id = str_prop

  -- Make sure the client has portal media roles
  str_prop = client.properties["pipewire.access.portal.media_roles"]
  if str_prop == nil then
    log:info(client, "Portal managed client did not set media_roles")
    return
  end
  media_roles = parseMediaRoles(str_prop)
  if (media_roles & MEDIA_ROLE_CAMERA) == 0 then
    log:info(client, "Ignoring portal check for clients without camera role")
    return
  end


  allowed = hasPermission(permissions, app_id, "yes")   --- Update permissions
  log:info(client, "setting permissions: " .. tostring(allowed))
  setPermissions(client, allowed, allowed)
end

clients_om = ObjectManager -- Create portal clients object manager
    {
      Interest {
        type = "client",
        Constraint {
          "pipewire.access",
          "=",
          "portal"
        },
      }
    }

-- Set permissions to portal clients from the permission store if loaded
pps_plugin = Plugin.find("portal-permissionstore")
if pps_plugin then
  nodes_om = ObjectManager {
    Interest {
      type = "node",
      Constraint {
        "media.role",
        "=",
        "Camera" },
      Constraint {
        "media.class", "=", "Video/Source" },
    }
  }
  nodes_om:activate()

  clients_om:connect("object-added", function(om, client)
    local new_perms = pps_plugin:call("lookup", "devices", "camera");
    updateClientPermissions(client, new_perms)
  end)

  nodes_om:connect("object-added", function(om, node)
    local new_perms = pps_plugin:call("lookup", "devices", "camera");
    for client in clients_om:iterate() do
      updateClientPermissions(client, new_perms)
    end
  end)
  pps_plugin:connect("changed", function(p, table, id, deleted, permissions)
    if table == "devices" or id == "camera" then
      for app_id, _ in pairs(permissions) do
        for client in clients_om:iterate {
          Constraint { "pipewire.access.portal.app_id", "=", app_id }
        } do
          updateClientPermissions(client, permissions)
        end
      end
    end
  end)
else
  clients_om:connect("object-added", function(om, client) -- Otherwise, just set all permissions to all portal clients
    local id = client["bound-id"]
    log:info(client, "Granting ALL access to client " .. id)
    client:update_permissions {
      ["any"] = "all" }
  end)
end

clients_om:activate()
