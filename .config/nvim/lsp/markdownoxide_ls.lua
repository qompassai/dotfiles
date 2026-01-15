-- /qompassai/Diver/lsp/markdown_oxide.lua
-- Qompass AI Diver Markdown Oxide LSP Config
-- Copyright (C) 2025 Qompass AI, All rights reserved
-- --------------------------------------------------
return ---@type vim.lsp.Config
{
    cmd = {
        'markdown-oxide',
    },
    filetypes = {
        'markdown',
    },
    root_markers = {
        '.git',
        '.obsidian',
        '.moxide.toml',
    },
    settings = {
        moxide = {
            dailynote = '%Y-%m-%d',
            heading_completions = true,
            title_headings = true,
            unresolved_diagnostics = true,
            semantic_tokens = true,
            tags_in_codeblocks = false,
        },
    },
}