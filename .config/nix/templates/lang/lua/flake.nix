# ~/.config/nix/templates/lang/lua.nix
# ------------------------------------
# Copyright (C) 2025 Qompass AI, All rights reserved
{
  description = "Comprehensive Lua AI development environment with multi-language bindings";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    rust-overlay.url = "github:oxalica/rust-overlay";
    zig-overlay.url = "github:mitchellh/zig-overlay";
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
    rust-overlay,
    zig-overlay,
  }:
    flake-utils.lib.eachDefaultSystem (system: let
      overlays = [
        (import rust-overlay)
        zig-overlay.overlays.default
      ];
      pkgs = import nixpkgs {inherit system overlays;};

      luaVersions = with pkgs; {
        default = openresty;
        lua51 = lua5_1;
        lua52 = lua5_2;
        lua53 = lua5_3;
        lua54 = lua5_4;
        luajit = luajit;
        openresty = openresty;
      };

      rustToolchain = pkgs.rust-bin.nightly.latest.default.override {
        extensions = ["clippy" "rust-analyzer" "rust-src" "rustfmt"];
        targets = [
          "aarch64-unknown-linux-gnu"
          "wasm32-unknown-unknown"
          "wasm32-wasi"
          "x86_64-unknown-linux-gnu"
        ];
      };

      pythonWithAI = pkgs.python3.withPackages (ps:
        with ps; [
          accelerate
          datasets
          jupyter
          keras
          lupa
          matplotlib
          nltk
          numpy
          opencv4
          pandas
          pillow
          polars
          pyarrow
          scikit-learn
          scipy
          seaborn
          spacy
          tensorflow
          torch
          torchvision
          transformers
        ]);

      luaAIPackages = with pkgs.luaPackages; [
        busted
        dkjson
        lua-cjson
        lua-resty-http
        luabitop
        luacheck
        luafilesystem
        luasocket
        penlight
      ];
    in {
      devShells = {
        default = self.devShells.${system}.full;

        ai = pkgs.mkShell {
          buildInputs = with pkgs; [
            cuda
            libtorch-bin
            luaVersions.default
            luarocks
            openblas
            pythonWithAI
            torch
          ];

          shellHook = ''
            echo "🤖 Lua AI Development Environment"
            echo "Primary Runtime: OpenResty LuaJIT 2.1 (Lua 5.1 compatible)"
            echo "Optimized for machine learning and AI applications"
          '';
        };

        full = pkgs.mkShell {
          buildInputs = with pkgs;
            [
              clang
              cmake
              gcc
              ninja
              pkg-config
              docker
              docker-compose
              postgresql
              redis
              sqlite
              direnv
              git
              just
              pandoc
              texlive.combined.scheme-full
              go
              golua
              luaVersions.default # PRIMARY: OpenResty LuaJIT 2.1
              luaVersions.lua51 # Legacy compatibility
              luaVersions.lua54 # Latest standard Lua
              luaVersions.luajit # Fallback: Standard LuaJIT
              lua-language-server # LSP
              luarocks # Package manager
              stylua # Formatter

              cargo-cross
              nodejs_20 # Node.js for Fengari
              pythonWithAI
              rustToolchain
              yarn
              zig

              cuda
              cudnn
              lapack
              libtorch-bin
              openblas
              torch

              hyperfine
              perf-tools
              valgrind
            ]
            ++ luaAIPackages;

          shellHook = ''
            echo "🤖 Comprehensive Lua AI Development Environment"
            echo "=================================================="
            echo ""
            echo "🌙 Primary Lua Runtime:"
            echo "  • OpenResty LuaJIT 2.1: $(openresty -v 2>&1 | head -1)"
            echo "    └── Lua 5.1 compatible, optimized for performance"
            echo ""
            echo "🔄 Additional Lua Versions:"
            echo "  • Lua 5.1: $(lua5.1 -v 2>&1)"
            echo "  • Lua 5.4: $(lua5.4 -v 2>&1)"
            echo "  • Standard LuaJIT: $(luajit -v 2>&1)"
            echo ""
            echo "🦀 Language Bindings:"
            echo "  • Go: $(go version)"
            echo "  • Node.js: $(node --version)"
            echo "  • Python: $(python3 --version)"
            echo "  • Rust: $(rustc --version)"
            echo "  • Zig: $(zig version)"
            echo ""
            echo "🧠 AI/ML Libraries:"
            echo "  • LibTorch: Available for C++ FFI"
            echo "  • PyTorch: $(python3 -c 'import torch; print(torch.__version__)' 2>/dev/null || echo 'Not available')"
            echo "  • TensorFlow: $(python3 -c 'import tensorflow as tf; print(tf.__version__)' 2>/dev/null || echo 'Not available')"
            echo ""
            echo "⚡ Performance Features:"
            echo "  • CUDA support: $(nvcc --version 2>/dev/null | head -1 || echo 'Not available')"
            echo "  • OpenBLAS for optimized linear algebra"
            echo "  • OpenResty LuaJIT 2.1 (fastest Lua runtime)"
            echo ""
            echo "🔧 Development Commands:"
            echo "  • just <task>                 # Run project tasks"
            echo "  • luarocks install <package>  # Install Lua packages"
            echo "  • pip install <package>       # Install Python packages"
            echo "  • cargo install <crate>       # Install Rust tools"
            echo ""
            echo "📚 Key Directories:"
            echo "  • benchmarks/   # Performance tests"
            echo "  • docs/         # Documentation"
            echo "  • lua/          # Lua source code"
            echo "  • python/       # Python AI scripts"
            echo "  • src/          # Rust/Zig/C bindings"
            echo ""

            # Set up environment variables for optimal performance (alphabetical)
            export CARGO_INCREMENTAL=0
            export CARGO_TARGET_DIR="./target"
            export LUA_CPATH="./lib/?.so;;"
            export LUA_PATH="./lua/?.lua;./lua/?/init.lua;;"
            export LUAJIT_ENABLE_LUA52COMPAT=1
            export OMP_NUM_THREADS=$(nproc)
            export RUSTC_WRAPPER="sccache"
            export TF_CPP_MIN_LOG_LEVEL=2
            export TORCH_USE_CUDA_DSA=1

            echo "Environment configured for high-performance Lua AI development! 🚀"
            echo "Default runtime: OpenResty LuaJIT 2.1 (Lua 5.1 compatible)"
          '';

          env = {
            CARGO_INCREMENTAL = "0";
            LUA_CPATH = "./lib/?.so;;";
            LUA_PATH = "./lua/?.lua;./lua/?/init.lua;;";
            LUAJIT_ENABLE_LUA52COMPAT = "1";
            OMP_NUM_THREADS = "$(nproc)";
            RUST_BACKTRACE = "1";
            TF_CPP_MIN_LOG_LEVEL = "2";
            TORCH_USE_CUDA_DSA = "1";
          };
        };

        minimal = pkgs.mkShell {
          buildInputs = with pkgs; [
            gcc
            lua-language-server
            luaVersions.default # OpenResty LuaJIT as default
            luarocks
            pkg-config
            stylua
          ];

          shellHook = ''
            echo "🌙 Minimal Lua Development Environment"
            echo "Primary Runtime: OpenResty LuaJIT 2.1 (Lua 5.1 compatible)"
            echo "OpenResty version: $(openresty -v 2>&1 | head -1)"
          '';
        };
      };

      packages = {
        lua-rust-example = pkgs.stdenv.mkDerivation {
          pname = "lua-rust-example";
          version = "0.1.0";

          src = ./.;

          buildInputs = with pkgs; [
            luaVersions.default
            pkg-config
            rustToolchain
          ];

          buildPhase = ''
            # Build Rust dynamic library for OpenResty LuaJIT
            cargo build --release

            # Copy to Lua library path (OpenResty/Lua 5.1 compatible)
            mkdir -p $out/lib/lua/5.1
            cp target/release/liblua_rust_example.so $out/lib/lua/5.1/rust_example.so
          '';
        };
      };
    });
}
