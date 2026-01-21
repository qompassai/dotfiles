-- /qompassai/dotfiles/.config/wireplumber/scripts/monitors/alsa-midi.lua
-- Qompass AI WirePlumber Alsa-Midi Monitors Script
-- Copyright (C) 2026 Qompass AI, All rights reserved
------------------------------------------------------------------------
cutils = require('common-utils') ---@type WPUtils
log = Log.open_topic('s-monitors') ---@type WPLog
defaults = {}
defaults.node_properties = { --- Midi bridge node properties
    ['factory.name'] = 'api.alsa.seq.bridge',
    ['node.name'] = 'Midi-Bridge', -- Name set for the node with ALSA MIDI ports
    ['priority.session'] = '100', -- Set priorities so that it can be used as a fallback driver (see pipewire#3562)
    ['priority.driver'] = '1',
}
config = {}
config.monitoring = Core.test_feature('monitor.alsa-midi.monitoring')
config.node_properties = Conf.get_section_as_properties('monitor.alsa-midi.properties', defaults.node_properties)
SND_PATH = '/dev/snd'
SEQ_NAME = 'seq'
SND_SEQ_PATH = SND_PATH .. '/' .. SEQ_NAME
midi_node = nil
fm_plugin = nil
--- Create and activate the ALSA MIDI bridge node.
---@return WPNode node The created and activated MIDI bridge node
function CreateMidiNode()
    local node = Node('spa-node-factory', config.node_properties)
    node:activate(Feature.Proxy.BOUND, function(n)
        local props = n.properties or {} -- n is the activated node; log its id/name for debugging
        log:info(
            string.format(
                'activated Midi bridge: id=%s name=%s',
                tostring(n.id or 'unknown'),
                tostring(props['node.name'] or 'Midi-Bridge')
            )
        )
    end)
    return node
end

if GLib.access(SND_SEQ_PATH, 'rw') then
    midi_node = CreateMidiNode()
elseif config.monitoring then
    fm_plugin = Plugin.find('file-monitor-api')
end
if midi_node == nil and fm_plugin ~= nil then --- Only monitor the MIDI device if file does not exist and plugin API is loaded
    fm_plugin:connect('changed', function(o, file, old, evtype) --- listen for changed events
        log:debug( --- basic debug info so o/old are not unused
            string.format(
                'file-monitor changed: plugin=%s file=%s evtype=%s',
                tostring(o),
                tostring(file),
                tostring(evtype)
            )
        )
        if evtype == 'attribute-changed' then
            if file ~= SND_SEQ_PATH then
                return
            end
            if old ~= nil then --- show previous attributes if available
                log:trace('previous attributes: ' .. tostring(old))
            end

            if midi_node == nil and GLib.access(SND_SEQ_PATH, 'rw') then
                midi_node = CreateMidiNode()
                fm_plugin:call('remove-watch', SND_PATH)
            end
        end

        if evtype == 'pre-unmount' then
            fm_plugin:call('remove-watch', SND_PATH)
        end
    end)
end
