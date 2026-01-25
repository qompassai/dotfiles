-- /qompassai/dotfiles/.config/wireplumber/scripts/metadata.lua
-- Qompass AI WirePlumber MetaData Script
-- Copyright (C) 2026 Qompass AI, All rights reserved
------------------------------------------------------------------------
--- @type WPMetadata
Metadata = Metadata
Script.async_activation = true
local args = ...
args = args:parse(1)
local metadata_name = args['metadata.name'] --- @type string
log = Log.open_topic('s-metadata')
log:info('creating metadata object: ' .. metadata_name)
impl_metadata = ImplMetadata(metadata_name) --- @type WPMetadata
impl_metadata:activate(Features.ALL, function(m, e)
    if e then
        Script:finish_activation_with_error('failed to activate the ' .. metadata_name .. ' metadata: ' .. tostring(e))
    else
        log:info('activated metadata object:', m)
        Script:finish_activation()
    end
end)
