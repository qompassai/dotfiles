# /qompassai/Diver/flake.nix
# ---------------------------------------
# Copyright (C) 2025 Qompass AI, All rights reserved
{
  description = "Qompass AI Diver - Reproducible Neovim config";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    neovim-nightly-overlay.url = "github:nix-community/neovim-nightly-overlay";
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
    neovim-nightly-overlay,
    ...
  }:
    flake-utils.lib.eachSystem [
      "aarch64-darwin"
      "aarch64-linux"
      "x86_64-darwin"
      "x86_64-linux"
    ] (system: let
      overlays = [neovim-nightly-overlay.overlays.default];
      pkgs = import nixpkgs {
        inherit system;
        overlays = overlays;
      };

      diver-nvim = pkgs.neovim-nightly.override {
        withNodeJs = true;
        withPython3 = true;
        withRuby = false;
        configure = {
          customRC = "";
          packages.myPlugins = with pkgs.vimPlugins; [
            LuaSnip
            cmp-digraphs
            coq.artifacts
            coq.thirdparty
            coq_nvim
            cord-nvim
            crates-nvim
            dressing-nvim
            friendly-snippets
            fzf-lua
            github-nvim-theme
            gruvbox-material
            guess-indent-nvim
            image-nvim
            jupynium-nvim
            jupytext-nvim
            lazy-nvim
            lazydev-nvim
            LazyVim
            legendary-nvim
            live-preview-nvim
            lualine-nvim
            luarocks
            mason-lspconfig-nvim
            mason-tool-installer-nvim
            mason-nvim
            material-nvim
            mini-ai
            molten-nvim
            nabla-nvim
            neo-tree-nvim
            neoconf-nvim
            nightfox-nvim
            noice-nvim
            none-ls-autoload-nvim
            none-ls-extras-nvim
            none-ls-jsonlint-nvim
            none-ls-luacheck-nvim
            none-ls-shellcheck-nvim
            none-ls-nvim
            nord-nvim
            nui-nvim
            nvim
            nvim-cmp
            nvim-colorizer-lua
            nvim-dap
            nvim-dap-python
            nvim-dap-ui
            nvim-dap-view
            nvim-dap-vscode-js
            nvim-jupyter
            nvim-lspconfig
            nvim-notify
            nvim-treesitter
            nvim-web-devicons
            onedark-nvim
            onedarkpro-nvim
            otter-nvim
            plenary-nvim
            quarto-nvim
            remote-nvim-nvim
            schemastore-nvim
            SchemaStore-nvim
            sqlite-lua
            telescope-zoxide
            telescope-nvim
            tokyonight-nvim
            transparent-nvim
            trouble-nvim
            typescript-nvim
            typst-preview-nvim
            venv-selector-nvim
            vim-dadbod-completion
            vim-gnupg
            vim-slime
            which-key-nvim
          ];
        };
      };
    in {
      apps.default = flake-utils.lib.mkApp {
        drv = diver-nvim;
      };

      devShells.default = pkgs.mkShell {
        buildInputs = [
          diver-nvim
          pkgs.fd
          pkgs.fzf
          pkgs.gcc
          pkgs.go
          pkgs.lua-language-server
          pkgs.nodejs
          pkgs.php
          pkgs.phpPackages.composer
          pkgs.poetry
          pkgs.python3
          pkgs.ripgrep
          pkgs.rust-analyzer
          pkgs.stylua
        ];
        shellHook = ''
          echo "🌊 Entering Diver shell. Run 'nvim' to launch."
        '';
      };
      packages.default = diver-nvim;
    });
}
