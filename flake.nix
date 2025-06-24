# /qompassai/dotfiles/flake.nix
{
  description = "Qompass AI Dotfiles";
  inputs = {
    flake-schemas.url =
      "https://flakehub.com/f/DeterminateSystems/flake-schemas/*";
    neovim = {
      url = "github:nix-community/neovim-nightly-overlay";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    nixpkgs.url = "https://flakehub.com/f/NixOS/nixpkgs/*";
    nix-on-droid.url = "github:nix-community/nix-on-droid";
  };
  outputs = { self, flake-schemas, nixpkgs, nix-on-droid, neovim }:
    let
      supportedSystems = [ "x86_64-linux" "aarch64-darwin" "aarch64-linux" ];
      forEachSupportedSystem = f:
        nixpkgs.lib.genAttrs supportedSystems (system:
          f {
            inherit (import nixpkgs {
              inherit system;
              overlays = [ neovim.overlays.default ];
            })
              pkgs;
          });
    in {
      inherit (flake-schemas) schemas;
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
            nix
            neomutt
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
            R
            rage
            sass
            sops
            sqlite
            steam
            tor-browser-bundle-bin
            unbound
            waybar
            wireguard-tools
            wget
            wofi
            zig
            zls
          ];
        };
      });
      nix-on-droid.configurations = {
        default = nix-on-droid.lib.config {
          modules = [ ./nix-on-droid.nix ];
          specialArgs = {
            inherit self nixpkgs;
            androidPackages = with self.nixpkgs.legacyPackages.aarch64-linux; [
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
}
