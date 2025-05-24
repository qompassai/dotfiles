--/qompassai/dotfiles/.config/wireplumber/main.lua.d/90-custom.lua
------------------------------------------------
-- Copyright (C) 2025 Qompass AI, All rights reserved

audio.processing = {
  aec_args = "analog_gain_control=0 digital_gain_control=1",
  agc_compression_gain = 9,
  agc_target_level = 3,
  enable_agc = true,
  enable_denoise = true,
  enable_ec = true,
  enable_ns = true,
  enable_resample = true,
  resample.disable_dither = false,
  resample.quality = 15,
}

context.properties = {
  cpu.cgroup = "high-priority.slice",
  cpu.scheduler.policy = "global",
  cpu.scheduler.priority = 80,
}

default_policy.policy = {
  allow_hw_offload = true,
  allow_rtkit = true,
  allow_wakeup = true,
  default_clock_allowed_rates = { 44100, 48000 },
  default_clock_force_quantum = 32,
  default_clock_max_quantum = 1024,
  default_clock_min_quantum = 32,
  default_clock_rate = 48000,
  media_session = {
    routes = { "builtin-output", "hdmi-output", "headphone-output" },
  },
  session_mode = "default-media",
}

memory = {
  mem.block-size = "64K",
  mem.reserved = "4G",
  mem.watermark = "32M",
}

network = {
  dscp.audio = 46,
  dscp.video = 34,
  dtls.key-exchange = "x448:kyber-1024",
  srtp.auth = "hmac-sha256-128",
  srtp.encryption = "aes-256-gcm",
}

performance = {
  allow_latency_adjustment = true,
  gpu.affinity = {
    ["intel"] = "8-15",
    ["nvidia"] = "0-7,16-23",
  },
  memlock.hard = 33554432,
  memlock.size = "unlimited",
  memlock.soft = 33554432,
  thread.priority = {
    ["audio"] = -15,
    ["quantum"] = -20,
    ["video"] = -10,
  },
}

power = {
  powersave.audio = false,
  powersave.video = "auto",
  suspend.disable = true,
}

video.processing = {
  framebuffer.drm-fourcc = "XR24",
  framebuffer.pool-size = 16,
  hdr.max_cll = "1000,500",
  hdr.metadata = "smpte2084;hibrid-log-gamma",
  nvenc.preset = "p6",
  nvenc.rc = "vbr_hq",
  nvenc.tune = "hq",
  prefer_hw_decoding = true,
  prefer_hw_encoding = true,
}

