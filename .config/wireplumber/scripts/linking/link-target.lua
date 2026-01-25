-- /qompassai/dotfiles/.config/wireplumber/scripts/linking/link-target.lua
-- Qompass AI WirePlumber Link-Target Linking Script
-- Copyright (C) 2026 Qompass AI, All rights reserved
----------------------------------------------------------------------------
lutils = require('linking-utils') ---@type WPUtils
cutils = require('common-utils') ---@type WPUtils
log = Log.open_topic('s-linking')
AsyncEventHook({
    name = 'linking/link-target',
    after = 'linking/prepare-link',
    interests = {
        EventInterest({
            Constraint({
                'event.type',
                '=',
                'select-target',
            }),
        }),
    },
    steps = {
        start = {
            next = 'none',
            execute = function(event, transition)
                local source, om, si, si_props, si_flags, target = lutils:unwrap_select_target_event(event)
                ---@cast om WPSessionItemManager
                ---@cast si WPSessionItem
                ---@cast si_props WPProperties
                ---@cast si_flags table
                ---@cast target WPSessionItem|nil
                if source then
                    log:info(source, 'select-target from source')
                end
                if not target then
                    transition:advance()
                    return
                end
                local target_props = target.properties ---@type WPProperties
                local out_item ---@type WPSessionItem
                local in_item ---@type WPSessionItem
                local si_link ---@type WPSessionItem
                local passthrough = si_flags.can_passthrough ---@type boolean
                log:info(
                    si,
                    string.format(
                        'handling item %d: %s (%s)',
                        si.id,
                        tostring(si_props['node.name']),
                        tostring(si_props['node.id'])
                    )
                )
                local exclusive = cutils.parseBool(si_props['node.exclusive']) ---@type boolean
                if
                    si_flags.failed_peer_id ~= nil
                    and si_flags.failed_peer_id == target.id
                    and si_flags.failed_count ~= nil
                    and si_flags.failed_count > 5
                then
                    transition:return_error('tried to link on last rescan, not retrying ' .. tostring(si_link))
                    return
                end
                if si_props['item.node.direction'] == 'output' then
                    out_item = si
                    in_item = target
                else
                    in_item = si
                    out_item = target
                end
                local is_role_policy_link = lutils.is_role_policy_target(si_props, target_props) ---@type boolean
                log:info(
                    si,
                    string.format(
                        'link %s <-> %s passthrough:%s, exclusive:%s, media role link:%s',
                        tostring(si_props['node.name']),
                        tostring(target_props['node.name']),
                        tostring(passthrough),
                        tostring(exclusive),
                        tostring(is_role_policy_link)
                    )
                )
                si_link = SessionItem('si-standard-link')
                local link_props = {
                    ['out.item'] = out_item, ---@type WPSessionItem
                    ['in.item'] = in_item, ---@type WPSessionItem
                    ['passthrough'] = passthrough, ---@type boolean
                    ['exclusive'] = exclusive, ---@type boolean
                    ['out.item.port.context'] = 'output', ---@type string
                    ['in.item.port.context'] = 'input', ---@type string
                    ['media.role'] = si_props['media.role'], ---@type WPPropValue
                    ['target.media.class'] = target_props['media.class'], ---@type WPPropValue
                    ['policy.role-based.priority'] = target_props['policy.role-based.priority'], ---@type WPPropValue
                    ['policy.role-based.action.same-priority'] = target_props['policy.role-based.action.same-priority'], ---@type WPPropValue
                    ['policy.role-based.action.lower-priority'] = target_props['policy.role-based.action.lower-priority'], ---@type WPPropValue
                    ['is.role.policy.link'] = is_role_policy_link,
                    ['main.item.id'] = si.id,
                    ['target.item.id'] = target.id, ---@type integer
                } ---@type WPProperties
                if not si_link:configure(link_props) then
                    transition:return_error('failed to configure si-standard-link ' .. tostring(si_link))
                    return
                end
                local ids = { si.id, target.id }
                si_link:connect('link-error', function(_, error_msg)
                    for _, id in ipairs(ids) do
                        local item = om:lookup({
                            Constraint({
                                'id',
                                '=',
                                id,
                                type = 'gobject',
                            }),
                        }) ---@type WPSessionItem|nil

                        if item then
                            local node = item:get_associated_proxy('node')
                            lutils.sendClientError(event, node, -32, error_msg)
                        end
                    end
                end)
                si_flags.was_handled = true
                si_flags.peer_id = target.id
                si_flags.failed_peer_id = target.id
                if si_flags.failed_count ~= nil then
                    si_flags.failed_count = si_flags.failed_count + 1
                else
                    si_flags.failed_count = 1
                end
                si_link:register()
                log:debug(si_link, 'registered link between ' .. tostring(si) .. ' and ' .. tostring(target))
                if not is_role_policy_link then
                    si_link:activate(Feature.SessionItem.ACTIVE, function(l, e)
                        if e then
                            transition:return_error(tostring(l) .. ' link failed: ' .. tostring(e))
                            if si_flags ~= nil then
                                si_flags.peer_id = nil
                            end
                            l:remove()
                        else
                            si_flags.failed_peer_id = nil
                            if si_flags.peer_id == nil then
                                si_flags.peer_id = target.id
                            end
                            si_flags.failed_count = 0
                            log:debug(l, 'activated link between ' .. tostring(si) .. ' and ' .. tostring(target))
                            transition:advance()
                        end
                    end)
                else
                    lutils.updatePriorityMediaRoleLink(si_link)
                    transition:advance()
                end
            end,
        },
    },
}):register()
