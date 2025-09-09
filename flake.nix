{
  description = "Qompass AI Dotfiles Flake";
  inputs = {
    devshell.url = "github:numtide/devshell";
    devshell.inputs.nixpkgs.follows = "nixpkgs";
    flake-compat.url = "github:edolstra/flake-compat";
    flake-compat.flake = false;
    flake-parts.url = "github:hercules-ci/flake-parts";
    flake-parts.inputs.nixpkgs-lib.follows = "nixpkgs";
    treefmt-nix.url = "github:numtide/treefmt-nix";
    treefmt-nix.inputs.nixpkgs.follows = "nixpkgs";
    nvfetcher.url = "github:berberman/nvfetcher";
    nvfetcher.inputs.nixpkgs.follows = "nixpkgs";
    nvfetcher.inputs.flake-compat.follows = "flake-compat";
    nixpkgs-unstable.url = "github:nixos/nixpkgs/nixos-unstable";
    nixos-stable.url = "github:nixos/nixpkgs/nixos-25.05";
  };
  outputs = inputs @ {
    self,
    nixpkgs,
    flake-parts,
    ...
  }:
    flake-parts.lib.mkFlake {inherit inputs;} {
      systems = ["x86_64-linux" "aarch64-linux"];
      imports = [
        inputs.flake-parts.flakeModules.easyOverlay
        inputs.devshell.flakeModule
        inputs.treefmt-nix.flakeModule
        ./flake
      ];
      packages = {
        x86_64-linux = let
          pkgs = import nixpkgs {system = "x86_64-linux";};
        in {
          userEnvironment = pkgs.buildEnv {
            name = "qompass-user-environment";
            paths = with pkgs; [
              ant
              burp
              caja
              carbonyl
              cava
              clamav
              composer
              connman
              discordo
              distcc
              docker
              fuzzel
              git
              limine
              neovim
              nyx
              python3
              rage
              rkhunter
              xdg-desktop-portal
              xdg-desktop-portal-hyprland
              wine
              wireguard
            ];
          };
        };
        aarch64-linux = let
          pkgs = import nixpkgs {system = "aarch64-linux";};
        in {
          userEnvironment = pkgs.buildEnv {
            name = "qompass-user-environment";
            paths = with pkgs; [
              git
              neovim
              python311
            ];
          };
        };
      };
    };
}
