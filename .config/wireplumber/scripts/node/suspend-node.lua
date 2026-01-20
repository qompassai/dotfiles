log = Log.open_topic('s-node')
sources = {}
SimpleEventHook({
    name = 'node/suspend-node',
    interests = {
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'node-state-changed',
            }),
            Constraint({
                'media.class',
                'matches',
                'Audio/*',
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
                'matches',
                'Video/*',
            }),
        }),
    },
    execute = function(event) ---@param event WPNodeEvent
        local node = event:get_subject()
        local new_state = event:get_properties()['event.subject.new-state']
        log:debug(node, 'changed state to ' .. new_state)
        local id = node['bound-id'] --- Always clear the current source if any
        if sources[id] then
            sources[id]:destroy()
            sources[id] = nil
        end
        if new_state == 'idle' or new_state == 'error' then --- Add a timeout source if idle for at least 5 seconds
            local timeout = tonumber(node.properties['session.suspend-timeout-seconds']) or 5 -- honor "session.suspend-timeout-seconds" if specified
            if timeout == 0 then
                return
            end
            sources[id] = Core.timeout_add(timeout * 1000, function()
                local active = node:get_active_features()
                if bit and bit.band(active, Feature.Proxy.BOUND) ~= 0 then
                    log:info(node, 'was idle for a while; suspending ...') --- Suspend the node but check first if the node still exists
                    node:send_command('Suspend')
                end

                sources[id] = nil -- Unref the source
                -- false (== G_SOURCE_REMOVE) destroys the source so that this
                -- function does not get fired again after 5 seconds
                return false
            end)
        end
    end,
}):register()
--[[log = Log.open_topic("s-node")
sources = {}
SimpleEventHook {
  name = "node/suspend-node",
  interests = {
    EventInterest {
      Constraint {
        "event.type",
        "=",
        "node-state-changed" },
      Constraint {
        "media.class", "matches", "Audio/*" },
    },
    EventInterest {
      Constraint {
        "event.type", "=", "node-state-changed" },
      Constraint {
        "media.class", "matches", "Video/*" },
    },
  },
  execute = function(event)
    local node = event:get_subject()
    local new_state = event:get_properties()["event.subject.new-state"]
    log:debug(node, "changed state to " .. new_state)
    -- Always clear the current source if any
    local id = node["bound-id"]
    if sources[id] then
      sources[id]:destroy()
      sources[id] = nil
    end


    if new_state == "idle" or new_state == "error" then --- Add a timeout source if idle for at least 5 seconds
      -- honor "session.suspend-timeout-seconds" if specified
      local timeout =
          tonumber(node.properties["session.suspend-timeout-seconds"]) or 5
      if timeout == 0 then
        return
      end

      sources[id] = Core.timeout_add(timeout * 1000,
        function() --- add idle timeout; multiply by 1000, timeout_add() expects ms
          -- Suspend the node
          -- but check first if the node still exists
          if (node:get_active_features() & Feature.Proxy.BOUND) ~= 0 then
            log:info(node, "was idle for a while; suspending ...")
            node:send_command("Suspend")
          end

          sources[id] = nil --- Unref the source
          -- false (== G_SOURCE_REMOVE) destroys the source so that this
          -- function does not get fired again after 5 seconds
          return false
        end)
    end
  end
}:register()
--]]
