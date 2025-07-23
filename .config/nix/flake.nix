# /qompassai/dotfiles/flake.nix
## Qompass AI Nix Flake Config
## Copyright (C) 2025 Qompass AI, All rights reserved
#####################################################
{
  description = "Qompass AI Nix Flake Config";
  inputs = {
    flake-parts.url = "github:hercules-ci/flake-parts";
    flake-schemas.url = "https://flakehub.com/f/DeterminateSystems/flake-schemas/*";
    flake-utils.url = "github:numtide/flake-utils";
    neovim = {
      url = "github:nix-community/neovim-nightly-overlay";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    nix-on-droid.url = "github:nix-community/nix-on-droid";
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
    nixpkgs-unstable.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = inputs @ {
    self,
    flake-parts,
    flake-schemas,
    flake-utils,
    nix-on-droid,
    nixpkgs,
    nixpkgs-unstable,
    neovim,
    ...
  }:
    flake-parts.lib.mkFlake {inherit inputs;} {
      systems = flake-utils.lib.defaultSystems;

      perSystem = {
        system,
        pkgs,
        ...
      }: let
        unstable = import nixpkgs-unstable {inherit system;};
      in {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            R
            blender
            btop
            cava
            chezmoi
            cmake
            conda
            curl
            docker
            dunst
            easyeffects
            firejail
            fish
            fuzzel
            gh
            git
            jq
            khal
            libreoffice
            lua
            maven
            mypaint
            neomutt
            neovim
            nix
            nixpkgs-fmt
            nodejs
            nvfetcher
            nvimpager
            pgadmin4
            pip
            pipewire
            pnpm
            postgresql
            python3
            python3Packages.pytest
            qt5ct
            qt6ct
            rage
            sass
            sops
            sqlite
            steam
            tor-browser-bundle-bin
            unbound
            waybar
            wget
            wireguard-tools
            wofi
            zig
            zls
            unstable.nil
          ];
        };
      };
      flake = {
        inherit (flake-schemas) schemas;
      };
      extraOutputs = {
        nix-on-droid.configurations = {
          default = nix-on-droid.lib.config {
            modules = [./nix-on-droid.nix];
            specialArgs = {
              inherit self nixpkgs;
              androidPackages = with nixpkgs.legacyPackages.aarch64-linux; [
                btop
                curl
                git
                jq
                neomutt
                nixpkgs-fmt
                python3
                sops
                wget
                wireguard-tools
                zls
              ];
            };
          };
        };
      };
    };
}
