# /qompassai/dotfiles/.config/qutebrowser/config.py
# Qompass AI QuteBrowser Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
config.load_autoconfig()
c.tabs.position = "top"
c.tabs.show = "multiple"
c.completion.shrink = True
c.messages.timeout = 3000
c.url.start_pages = ["about:blank"]
c.url.default_page = "about:blank"
c.url.searchengines = {"DEFAULT": "https://duckduckgo.com/?q={}"}
config.bind('J', 'tab-prev')
config.bind('K', 'tab-next')
config.bind('H', 'back')
config.bind('L', 'forward')
config.bind('gi', 'hint inputs')
config.bind('yy', 'yank')
config.bind('p', 'open -- {clipboard}')
config.bind('P', 'open -t -- {clipboard}')
config.bind('d', 'tab-close')
config.bind('u', 'undo')
config.bind('x', 'tab-close')
config.bind('X', 'undo')
config.bind('r', 'reload')
config.bind('R', 'reload -f')
config.bind('<Ctrl-o>', 'back')
config.bind('<Ctrl-i>', 'forward')
config.bind('gg', 'scroll-to-perc 0')
config.bind('G', 'scroll-to-perc 100')
config.bind('h', 'scroll left')
config.bind('j', 'scroll down')
config.bind('k', 'scroll up')
config.bind('l', 'scroll right')
config.bind('zz', 'scroll center')
config.bind('/', 'set-cmd-text /')
config.bind('?', 'set-cmd-text ?')
config.bind('n', 'search-next')
config.bind('N', 'search-prev')
config.bind('<Ctrl-f>', 'rl-forward-char', mode='command')
config.bind('<Ctrl-b>', 'rl-backward-char', mode='command')
config.bind('<Ctrl-a>', 'rl-beginning-of-line', mode='command')
config.bind('<Ctrl-e>', 'rl-end-of-line', mode='command')
config.bind('<Ctrl-u>', 'rl-unix-line-discard', mode='command')
config.bind('<Ctrl-w>', 'rl-unix-word-rubout', mode='command')
config.bind('<Ctrl-k>', 'rl-kill-line', mode='command')
c.hints.uppercase = True
c.hints.chars = "asdfhjklwertyuiopzxcvbnm"
c.statusbar.show = "in-mode"
c.downloads.position = "bottom"
c.content.javascript.enabled = True
c.colors.completion.fg = "#b8bb26"
c.colors.completion.odd.bg = "#282828"
c.colors.completion.even.bg = "#3c3836"
c.colors.tabs.even.bg = "#1d2021"
c.colors.tabs.odd.bg = "#1d2021"
c.colors.statusbar.normal.bg = "#282828"
c.colors.statusbar.insert.bg = "#458588"
c.colors.statusbar.passthrough.bg = "#b16286"
c.colors.statusbar.caret.bg = "#fe8019"
c.colors.statusbar.command.bg = "#282828"
pylint: disable=C0111
c = c  # noqa: F821 pylint: disable=E0602,C0103
config = config  # noqa: F821 pylint: disable=E0602,C0103
