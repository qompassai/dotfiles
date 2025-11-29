-- /qompassai/Diver/lsp/stylua.lua
-- Qompass AI Stylua LSP Spec
-- Copyright (C) 2025 Qompass AI, All rights reserved
------------------------------------------------------
vim.lsp.config["stylua"] = {
  cmd = {
    "stylua",
  },
  filetypes = {
    "lua",
    "luau",
  },
  codeActionProvider = false,
  colorProvider = false,
  semanticTokensProvider = nil,
  settings = {
    stylua = {},
  },
}
