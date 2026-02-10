#!/usr/bin/env bash
# /qompassai/dotfiles/.config/pipewire/pw.sh
# Qompass AI Pipewire Setup Script
# Copyright (C) 2026 Qompass AI, All rights reserved
# ========================================================================
set -e
CONF_DIR="$HOME/.config/pipewire/pipewire.conf.d"
mkdir -p "$CONF_DIR"
cat > "$CONF_DIR/10-properties.conf" << 'EOF'
# /qompassai/dotfiles/.config/pipewire/pipewire.conf.d/10-properties.conf
# ==========================================================================
context.properties = {
    clock.power-of-two-quantum                                  = true
    core.daemon                                                 = true
    core.name                                                   = pipewire-0
    cpu.zero.denormals                                          = true
    context.data-loop.library.name.system                       = support/libspa-support
    context.num-data-loops                       = 1
    library.name.system                          = support/libspa-support
    link.max-buffers                             = 64
    log.level                                    = 5
    # log.patterns                               = [ "*:E" "*:W" ]
    mem.allow-mlock                              = true
    mem.mlock-all                                = false
    mem.warn-mlock                               = false
    # rlimit.nofile                              = -1
    support.dbus                                 = true
}
EOF
cat > "$CONF_DIR/20-clock.conf" << 'EOF'
# /qompassai/dotfiles/.config/pipewire/pipewire.conf.d/20-clock.conf
# ==========================================================================
context.properties = {
    default.clock.allowed-rates                  = [ 44100 48000 88200 96000 ]
    default.clock.rate                           = 48000
    # default.clock.force-rate                   = 0
    default.clock.max-quantum                    = 2048
    default.clock.min-quantum                    = 128
    default.clock.quantum                        = 128
    default.clock.quantum-floor                  = 4
    default.clock.quantum-limit                  = 8192
    # default.clock.force-quantum                = 0
    default.video.height                         = 1080
    default.video.rate.denom                     = 1 
    default.video.rate.num                       = 60
    default.video.width                          = 1920
    # resample.disable                           = false
    # resample.quality                           = 10
    settings.check-quantum                       = false
    settings.check-rate                          = false
}
EOF
cat > "$CONF_DIR/30-rules.conf" << 'EOF'
# /qompassai/dotfiles/.config/pipewire/pipewire.conf.d/30-rules.conf
# ==========================================================================
context.properties.rules = [
    {   matches = [ { cpu.vm.name = !null } ]
        actions = {
            update-props = {
                default.clock.min-quantum
                default.clock.quantum            = 2048
            }
        }
    }
    # {   matches = [ { device.power-profile = "power-saver" } ]
    #     actions = {
    #         update-props = {
    #             default.clock.quantum        = 2048
    #         }
    #     }
    # }
]
EOF
cat > "$CONF_DIR/40-spa-libs.conf" << 'EOF'
# /qompassai/dotfiles/.config/pipewire/pipewire.conf.d/40-spa-libs.conf
# ==========================================================================
context.spa-libs = {
    api.alsa.*                                   = alsa/libspa-alsa
    api.bluez5.*                                 = bluez5/libspa-bluez5
    # api.jack.*                                 = jack/libspa-jack
    audio.convert.*                              = audioconvert/libspa-audioconvert
    avb.*                                        = avb/libspa-avb
    support.*                                    = support/libspa-support
    api.libcamera.*                              = libcamera/libspa-libcamera 
    api.v4l2.*                                   = v4l2/libspa-v4l2
    api.vulkan.*                                 = vulkan/libspa-vulkan
    video.convert.*                              = videoconvert/libspa-videoconvert
    # filter.graph                               = filter-graph/libspa-filter-graph
    # audiotestsrc                               = audiotestsrc/libspa-audiotestsrc
    # videotestsrc                               = videotestsrc/libspa-videotestsrc
}
EOF
cat > "$CONF_DIR/50-modules-core.conf" << 'EOF'
# /qompassai/dotfiles/.config/pipewire/pipewire.conf.d/50-modules-core.conf
# ==========================================================================
context.modules = [
    { name = libpipewire-module-rt
        args = {
            nice.level                           = -11
            rt.prio                              = 95 
            rt.time.hard                         = -1
            rt.time.soft                         = -1
            # uclamp.max                         = 1024
            # uclamp.min                         = 0
        }
        flags      = [ ifexists nofail ]
        condition  = [ { module.rt = !false } ]
    }
    
    { name = libpipewire-module-protocol-native
        args = {
            # servers = [ { address = "unix:native" } ]
        }
    }
    { name = libpipewire-module-profiler
        args = {
            # profile.interval.ms              = 0
        }
        condition = [ { module.profiler = !false } ]
    }
    { name = libpipewire-module-metadata
        condition = [ { module.metadata = !false } ]
    }
    { name = libpipewire-module-spa-device-factory
        condition = [ { module.spa-device-factory = !false } ]
    }
    { name = libpipewire-module-spa-node-factory
        condition = [ { module.spa-node-factory = !false } ]
    }
    { name = libpipewire-module-client-node
        condition = [ { module.client-node = !false } ]
    }
    { name = libpipewire-module-client-device
        condition = [ { module.client-device = !false } ]
    }
    { name = libpipewire-module-portal
        flags     = [ ifexists nofail ]
        condition = [ { module.portal = !false } ]
    }
    { name = libpipewire-module-access 
        args = {
            # access.allowed                   = [ "flatpak" ]
            # access.rejected                  = [ "snapd" ]
            # access.legacy                    = true
        }
        condition = [ { module.access = !false } ]
    }
    { name = libpipewire-module-adapter
        condition = [ { module.adapter = !false } ]
    }
    
    ## Graph Management
    { name = libpipewire-module-link-factory
        args = {
            # allow.link.passive               = false
        }
        condition = [ { module.link-factory = !false } ]
    }
    { name = libpipewire-module-session-manager          # Session manager support (WirePlumber)
        condition = [ { module.session-manager = !false } ]
    }
]
EOF
cat > "$CONF_DIR/55-modules-audio.conf" << 'EOF'
# /qompassai/dotfiles/.config/pipewire/pipewire.conf.d/55-modules-audio.conf
# ==========================================================================
context.modules = [
    { name = libpipewire-module-echo-cancel
        args = {
            library.name                         = aec/libspa-aec-webrtc
            aec.args = {
                # webrtc.extended_filter         = true   # Extended filter mode
                # webrtc.intelligibility_enhancer= true   # Speech intelligibility
                # webrtc.noise_suppression       = true   # Noise suppression
                # webrtc.gain_control            = true   # Automatic gain control
                # webrtc.experimental_agc        = true   # Experimental AGC
                # webrtc.delay_agnostic          = true   # Delay-agnostic mode
            }
            capture.props = {
                node.name                        = "Echo-Cancel-Capture"
                node.passive                     = true
                audio.channels                   = 2
                audio.position                   = [ FL FR ]
            }
            source.props = {
                node.name                        = "Echo-Cancel-Source"
                audio.channels                   = 2
                audio.position                   = [ FL FR ]
            }
            sink.props = {
                node.name                        = "Echo-Cancel-Sink"
                audio.channels                   = 2
                audio.position                   = [ FL FR ]
            }
            playback.props = {
                node.name                        = "Echo-Cancel-Playback"
                node.passive                     = true
                audio.channels                   = 2
                audio.position                   = [ FL FR ]
            }
        }
        flags     = [ ifexists nofail ]
        condition = [ { module.echo-cancel = !false } ]
    }
    # { name = libpipewire-module-filter-chain
    #     args = {
    #         node.name                        = "Audio-Filters"
    #         node.description                 = "Audio Filter Chain"
    #         media.class                      = "Audio/Sink"
    #         audio.position                   = [ FL FR ]
    #         filter.graph = {
    #             nodes = [
    #                 { type = ladspa name = "compressor" plugin = "sc4_1882" }
    #                 { type = builtin name = "eq" control = { Freq = 100 Gain = 3.0 } }
    #             ]
    #             links = [
    #                 { output = "compressor:Out" input = "eq:In" }
    #             ]
    #         }
    #     }
    #     flags     = [ ifexists nofail ]
    #     condition = [ { module.filter-chain = true } ]
    # }
]
EOF
cat > "$CONF_DIR/60-modules-optional.conf" << 'EOF'
# /qompassai/dotfiles/.config/pipewire/pipewire.conf.d/60-modules-optional.conf
# ==========================================================================
context.modules = [
    { name = libpipewire-module-x11-bell
        args = {
            sample.name                          = "bell-window-system"
            sink.name                            = "@DEFAULT_SINK@"
            x11.display                          = null    # Auto-detect
            # x11.xauthority                     = null    # Auto-detect
        }
        flags     = [ ifexists nofail ]
        condition = [ { module.x11.bell = !false } ]
    }
    { name = libpipewire-module-jackdbus-detect
        args = {
            jack.client-name                     = PipeWire
            jack.connect                         = true
            jack.library                         = libjack.so.0
            # jack.server                        = null
            tunnel.mode                          = duplex  # source|sink|duplex
            source.props = {
                audio.channels                   = 2
                audio.position                   = [ FL FR ]
                # midi.ports                     = 1
                # node.name                      = "JACK-Source"
            }
            sink.props = {
                audio.channels                   = 2
                audio.position                   = [ FL FR ]
                # midi.ports                     = 1
                # node.name                      = "JACK-Sink"
            }
        }
        flags     = [ ifexists nofail ]
        condition = [ { module.jackdbus-detect = !false } ]
    }
    # { name = libpipewire-module-loopback
    #     args = {
    #         node.description                 = "Audio Loopback"
    #         capture.props = {
    #             node.name                    = "loopback-capture"
    #             audio.position               = [ FL FR ]
    #             stream.dont-remix            = true
    #             node.passive                 = true
    #         }
    #         playback.props = {
    #             node.name                    = "loopback-playback"
    #             audio.position               = [ FL FR ]
    #             stream.dont-remix            = true
    #             node.passive                 = true
    #         }
    #     }
    #     flags     = [ ifexists nofail ]
    #     condition = [ { module.loopback = true } ]
    # }
]
EOF
cat > "$CONF_DIR/70-objects.conf" << 'EOF'
# /qompassai/dotfiles/.config/pipewire/pipewire.conf.d/70-objects.conf
# ==========================================================================
context.objects = [
    { factory = spa-node-factory
        args = {
            clock.id                             = monotonic  # realtime|tai|monotonic-raw|boottime
            # clock.name                         = "clock.system.monotonic"
            factory.name                         = support.node.driver
            node.group                           = pipewire.dummy
            node.name                            = Dummy-Driver
            node.sync-group                      = sync.dummy
            priority.driver                      = 200000
        }
        condition = [ { factory.dummy-driver = !false } ]
    }
    { factory = spa-node-factory
        args = {
            factory.name                         = support.node.driver
            node.freewheel                       = true
            node.group                           = pipewire.freewheel
            node.name                            = Freewheel-Driver
            node.sync-group                      = sync.dummy
            priority.driver                      = 190000
            # freewheel.wait                     = 10      # Wait time in ms
        }
        condition = [ { factory.freewheel-driver = !false } ]
    }
    # { factory = adapter
    #     args = {
    #         factory.name                     = support.null-audio-sink
    #         node.name                        = "Virtual-Sink"
    #         node.description                 = "Virtual Audio Sink"
    #         media.class                      = "Audio/Sink"
    #         audio.position                   = [ FL FR ]
    #         monitor.channel-volumes          = true
    #         monitor.passthrough              = false
    #     }
    # }
    
    # { factory = adapter
    #     args = {
    #         factory.name                     = support.null-audio-sink
    #         node.name                        = "Virtual-Source"
    #         node.description                 = "Virtual Microphone"
    #         media.class                      = "Audio/Source/Virtual"
    #         audio.position                   = [ FL FR ]
    #         monitor.passthrough              = true
    #     }
    # }
]
EOF

cat > "$CONF_DIR/80-multicore.conf.disabled" << 'EOF'
# /qompassai/dotfiles/.config/pipewire/pipewire.conf.d/80-multicore.conf
# ==========================================================================
context.properties = {
    context.num-data-loops                       = 4 
}
context.data-loops = [
    {   loop.class                               = [ data.rt audio.rt ]
        loop.rt-prio                             = 88
        thread.affinity                          = [ 0 1 ]
        thread.name                              = data-loop.0
    }
    {   loop.class                               = [ data.rt audio.rt ]
        loop.rt-prio                             = 88
        thread.affinity                          = [ 2 3 ]
        thread.name                              = data-loop.1
    }
    {   loop.class                               = [ data.rt audio.rt ]
        loop.rt-prio                             = 88
        thread.affinity                          = [ 4 5 ]
        thread.name                              = data-loop.2
    }
    {   loop.class                               = [ data.rt audio.rt ]
        loop.rt-prio                             = 88
        thread.affinity                          = [ 6 7 ]
        thread.name                              = data-loop.3
    }
]
EOF
cat > "$CONF_DIR/90-low-latency.conf.disabled" << 'EOF'
# /qompassai/dotfiles/.config/pipewire/pipewire.conf.d/90-low-latency.conf
# ==========================================================================
context.properties = {
    default.clock.max-quantum                    = 1024
    default.clock.min-quantum                    = 64
    default.clock.quantum                        = 64
}
EOF
cat > "$CONF_DIR/95-battery-saver.conf.disabled" << 'EOF'
# /qompassai/dotfiles/.config/pipewire/pipewire.conf.d/95-battery-saver.conf
# ==========================================================================
context.properties = {
    default.clock.quantum                        = 2048
    resample.quality                             = 2
    # module.echo-cancel                         = false
    # module.filter-chain                        = false
}
EOF
echo ""
echo "✅ Created modular PipeWire configuration:"
echo "   Location: $CONF_DIR/"
echo ""
echo "📁 Configuration files:"
ls -1 "$CONF_DIR/" | while read file; do
    if [[ $file == *.disabled ]]; then
        echo "   ⚪ $file (disabled)"
    else
        echo "   ✅ $file"
    fi
done

echo ""
echo "🔧 Optional Features (rename .disabled to .conf to enable):"
echo "   • 80-multicore.conf.disabled     - Multi-core CPU optimization"
echo "   • 90-low-latency.conf.disabled   - Ultra-low latency (64 samples)"
echo "   • 95-battery-saver.conf.disabled - Battery/power saving mode"

systemctl --user restart pipewire pipewire-pulse wireplumber
sleep 2
pw-cli info 0 | grep -i properties
echo "PipeWire setup complete!"
