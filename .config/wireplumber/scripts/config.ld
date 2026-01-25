-- /qompassai/dotfiles/.config/config.ld
-- Qompass AI WirePlumber LuaDoc Config
-- Copyright (C) 2026 Qompass AI, All rights reserved
-- ----------------------------------------
project = 'Qompass AI WirePlumber Policy'
title = 'Qompass AI WirePlumber Policy Reference'
description = [[
WirePlumber Gets JITty with it.
]]
dir = 'docs'
ext = 'md'
format = 'markdown'
one = false
simple = false
style = '!'
template = '!'
tparam = true
use_markdown_titles = true
file = {
    'lua/types/config/wp.lua',
    'scripts',
}
package = '.'
merge = true
unqualified = true
all = true
quiet = false
fatalwarnings = false
no_args_infer = false
boilerplate = true
multimodule = true
colon = true
lls = true
date = ''
