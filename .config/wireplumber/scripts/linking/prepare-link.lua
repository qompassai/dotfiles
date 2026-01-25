-- /qompassai/dotfiles/.config/wireplumber/scripts/linking/prepare-link.lua
-- Qompass AI WirePlumber Link-Target Linking Script
-- Copyright (C) 2026 Qompass AI, All rights reserved
------------------------------------------------------------------------
local bit = bit or require('bit32')
lutils = require('linking-utils')
cutils = require('common-utils') ---@type WPUtils
log = Log.open_topic('s-linking')
SimpleEventHook({
    name = 'linking/prepare-link',
    interests = {
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'select-target',
            }),
        }),
    },
    execute = function(event)
        local source, si_mgr, si, si_props, si_flags, target = lutils:unwrap_select_target_event(event)
        ---@cast source WPObject
        ---@cast si_mgr WPSessionItemManager
        ---@cast si WPSessionItem
        ---@cast si_props WPProperties
        ---@cast si_flags table
        ---@cast target WPSessionItem|nil
        local mgr_first = si_mgr:get_managed_object() and si_mgr:get_managed_object(nil) or nil
        local mgr_id = mgr_first and mgr_first.id or -1
        log:debug(source, string.format('prepare-link: manager=%d, item=%d', mgr_id, si.id))
        local si_id = si.id
        local reconnect = not cutils.parseBool(si_props['node.dont-reconnect'])
        local exclusive = cutils.parseBool(si_props['node.exclusive'])
        local si_must_passthrough = cutils.parseBool(si_props['item.node.encoded-only'])
        log:info(
            si,
            string.format(
                'handling item %d: %s (%s)',
                si_id,
                tostring(si_props['node.name']),
                tostring(si_props['node.id'])
            )
        )
        if si_flags.peer_id then
            if target and si_flags.peer_id == target.id then
                log:info(si, '... already linked to proper target')
                if Settings.get_boolean('linking.follow-default-target') and si_flags.has_node_defined_target then
                    lutils:checkFollowDefault(si, target)
                end
                target = nil
                goto done
            end
            local link = lutils.lookupLink(si_id, si_flags.peer_id) ---@cast link WPSessionItemLink|nil
            if reconnect then
                if link ~= nil then
                    local link_feats = link:get_active_features()
                    if bit.band(link_feats, Feature.SessionItem.ACTIVE) == 0 then
                        log:warning(link, 'Link was not activated before removing')
                    end
                    si_flags.peer_id = nil ---@type integer
                    link:remove()
                    log:info(si, '... moving to new target')
                end
            else
                if link ~= nil then
                    log:info(si, '... dont-reconnect, not moving')
                    goto done
                end
            end
        end
        if not reconnect and si_flags.was_handled then
            target = nil
            goto done
        end
        if target then
            local target_is_linked, target_is_exclusive = lutils.isLinked(target)
            if target_is_exclusive then
                log:info(si, '... target is linked exclusively')
                target = nil
            end
            if target_is_linked then
                if exclusive or si_must_passthrough then
                    log:info(si, '... target is already linked, cannot link exclusively')
                    target = nil
                else
                    si_flags.can_passthrough = false
                end
            end
        end
        if not target then
            log:info(si, '... target not found, reconnect:' .. tostring(reconnect))
            local node = si:get_associated_proxy('node') ---@cast node WPNode|nil
            if reconnect and si_flags.was_handled then
                log:info(si, '... waiting reconnect')
                return
            end
            local linger = cutils.parseBool(si_props['node.linger'])
            if linger then
                log:info(si, '... node linger')
                return
            end
            lutils.sendClientError(event, node, -2, reconnect and 'no target node available' or 'target not found')
            if not reconnect and node then
                log:info(si, '... destroy node')
                node:request_destroy()
            end
        end
        ::done::
        event:set_data('target', target)
    end,
}):register()
