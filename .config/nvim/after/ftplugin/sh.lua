-- /qompassai/Diver/after/ftplugin/sh.lua
-- Qompass AI Diver After Filetype Shell Config
-- Copyright (C) 2026 Qompass AI, All rights reserved
-- ----------------------------------------
vim.api.nvim_create_autocmd('BufWritePre',
  {
    pattern = {
      '*.sh'
    },
    callback = function(args)
      vim.lsp.format({
        bufnr = args.buf,
        async = true,
      })
    end,
  })