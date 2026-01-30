-- lua.lua
-- Qompass AI - [ ]
-- Copyright (C) 2026 Qompass AI, All rights reserved
-- ----------------------------------------
local names = {
    'allowrevins',
    'ambiwidth',
    'autochdir',
    'autocomplete',
    'autocompletedelay',
    'autoread',
    'autowrite',
    'autowriteall',
    'background',
    'backspace',
    'backup',
    'backupcopy',
    'breakindent',
    'clipboard',
    'cmdheight',
    'comments:append',
    'completeitemalign',
    'completeopt',
    'complete:remove',
    'concealcursor',
    'conceallevel',
    'confirm',
    'cursorbind',
    'cursorline',
    'cursorlineopt',
    'debug',
    'deprecation_warnings',
    'diffopt',
    'editorconfig',
    'encoding',
    'errorbells',
    'exrc',
    'expandtab',
    'fileencoding',
    'fileencodings',
    'fileformats',
    'foldenable',
    'foldexpr',
    'foldlevel',
    'foldmethod',
    'formatoptions',
    'git_command_ssh',
    'grepprg',
    'guicursor',
    'guipty',
    'hidden',
    'highlight',
    'history',
    'hlsearch',
    'icon',
    'ignorecase',
    'iminsert',
    'imsearch',
    'inccommand',
    'incsearch',
    'isprint',
    'joinspaces',
    'jumpoptions',
    'langnoremap',
    'laststatus',
    'lazyredraw',
    'lhistory',
    'linebreak',
    'linespace',
    'lisp',
    'lispwords',
    'list',
    'listchars',
    'loaded_illuminate',
    'loaded_netrw',
    'loaded_netrwPlugin',
    'loaded_perl_provider ',
    'loaded_python_provider',
    'loaded_ruby_provider',
    'magic',
    'mapleader',
    'mat',
    'maxsearchcount',
    'mkdp_theme',
    'modeline',
    'modelines',
    'modifiable',
    'mouse',
    'mousescroll',
    'node_host_prog',
    'nrformats',
    'number',
    'packpath',
    'pumheight',
    'python3_host_prog',
    'redrawtime',
    'relativenumber',
    'report',
    'ruby_host_prog',
    'ruff_makeprg_params',
    'ruler',
    'rust_cargo_check_all_targets',
    'rust_conceal',
    'rust_conceal_pub',
    'rust_playpen_url',
    'rust_recommended_style',
    'rust_shortener_url',
    'rustfmt_detect_version',
    'rustfmt_emit_files',
    'scrolloff',
    'secure',
    'semantic_tokens_enabled',
    'sessionopts',
    'shiftwidth',
    'shortmess',
    'showmode',
    'showtabline',
    'sidescroll',
    'sidescrolloff',
    'smartcase',
    'smarttab',
    'smoothscroll',
    'softtabstop',
    'spell',
    'spellfile',
    'spelllang',
    'spelloptions',
    'splitbelow',
    'splitright',
    'sqlite_clib_path',
    'startofline',
    'swapfile',
    'switchbuf',
    'syntax',
    'syntax_on',
    'table_mode_always_active',
    'table_mode_corner',
    'table_mode_separator',
    'table_mode_syntax',
    'tabpagemax',
    'tabstop',
    'tags',
    'termguicolors',
    'textwidth',
    'timeout',
    'timeoutlen',
    'title',
    'tm',
    'ttimeoutlen',
    'ttyfast',
    'undodir',
    'undofile',
    'updatetime',
    'use_blink_cmp',
    'vim_markdown_folding_disabled',
    'vim_markdown_follow_anchor',
    'vim_markdown_frontmatter',
    'vim_markdown_json_frontmatter',
    'vim_markdown_math',
    'viminfo:append',
    'virtualedit',
    'which_key_disable_health_check',
    'wildignore',
    'wildmenu',
    'wildmode',
    'winborder',
    'wrap',
    'writebackup',
}

local function scope_to_ns(scope)
    if scope == 'win' then
        return 'wo'
    end
    if scope == 'buf' then
        return 'bo'
    end
    if scope == 'global' then
        return 'o'
    end
    return 'o(?)' -- fallback, should be rare
end

local function opt_type_to_lua(t)
    if t == 'boolean' then
        return 'boolean'
    end
    if t == 'number' then
        return 'integer'
    end -- vim options use Number; most are integers
    if t == 'string' then
        return 'string'
    end
    return tostring(t)
end

for _, n in ipairs(names) do
    local ok, info = pcall(vim.api.nvim_get_option_info2, n, {})
    if ok then
        local ns = scope_to_ns(info.scope)
        local ty = opt_type_to_lua(info.type)
        print(string.format('%-16s  ns=%-3s  type=%-7s  (opt)', n, ns, ty))
    else
        print(string.format('%-16s  ns=%-3s  type=%-7s  (NOT AN OPTION; maybe vim.g)', n, 'g', 'any'))
    end
end