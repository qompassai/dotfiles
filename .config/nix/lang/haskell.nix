# ~/.config/nix/lang/haskell.nix
# ------------------------------
# Copyright (C) 2025 Qompass AI, All rights reserved
{pkgs ? import <nixpkgs> {}}:
pkgs.mkShell {
  buildInputs = [
    pkgs.haskellPackages.ghc
    pkgs.haskellPackages.stack
    pkgs.zlib
  ];

  shellHook = ''
    export STACK_ROOT="$HOME/.nix/stack"
    export PATH="$HOME/.nix/store/bin:$PATH"
  '';
}
