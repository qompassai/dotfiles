#/qompassai/dotfiles/flake.nix
# ----------------------------
# Copyright (C) 2025 Qompass AI, All rights reserved
{
  description = "Qompass AI Dotfiles";
  inputs = {
    flake-schemas.url = "https://flakehub.com/f/DeterminateSystems/flake-schemas/*";
    nixpkgs.url = "https://flakehub.com/f/NixOS/nixpkgs/*";
  };
  outputs = { self, flake-schemas, nixpkgs }:
    let
      supportedSystems = [ "x86_64-linux" "aarch64-darwin" "aarch64-linux" ];
      forEachSupportedSystem = f: nixpkgs.lib.genAttrs supportedSystems (system: f {
        pkgs = import nixpkgs { inherit system; };
      });
    in {
      schemas = flake-schemas.schemas;
      devShells = forEachSupportedSystem ({ pkgs }: {
        default = pkgs.mkShell {
          packages = with pkgs; [
            blender
            btop
            cava
            chezmoi
            cmake
            conda
            curl
            docker
            dunst
            fish
            gh
            git
            ipython
            jq
            libreoffice
            lua
            maven
            neomutt
            nixpkgs-fmt
            nodejs
            pip
            pnpm
            postgresql
            python3
            python3Packages.pytest
            qt5ct
            qt6ct
            R
            sass
            sqlite
            steam
            tor-browser-bundle-bin
            waybar
            wireguard-tools
            wget
            wofi
            zig
            zls
          ];
        };
      });
    };
}
