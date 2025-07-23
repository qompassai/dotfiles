# ~/.config/nixpkgs/overlays/neovim-nightly.nix
# ---------------------------------------------
# Copyright (C) 2025 Qompass AI, All rights reserved

let neovim-nightly-overlay = import (builtins.fetchTarball { 
  url = https://github.com/nix-community/neovim-nightly-overlay/archive/master.tar.gz; 
}); 
in self: super: { 
  inherit (neovim-nightly-overlay self super) neovim-nightly; 
}

