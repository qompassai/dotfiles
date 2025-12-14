#!/usr/bin/env sh
# /qompassai/Shell/.profile.d/56-ocaml.sh
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
export DUNE_CACHE=enabled
export DUNE_CACHE_ROOT="$HOME/.cache/dune"
export OCAMLFORMAT_PROFILE=conventional
export OCAMLPARAM=""
export OCAMLRUNPARAM="b"
export OPAMROOT="$HOME/.opam"
export OPAM_SWITCH_PREFIX="$HOME/.opam/default"
export UTOP_HISTORY="$HOME/.utop-history"
export PATH="$HOME/.opam/default/bin:$PATH"
if [ -r "$HOME/.opam/opam-init/init.sh" ]; then
    . "$HOME/.opam/opam-init/init.sh" >/dev/null 2>/dev/null || true
fi
ocamlproject() {
    local project_name="${1:-new-ocaml-project}"
    mkdir -p "$project_name"
    cd "$project_name" || return 1

    dune init project "$project_name"

    echo "*.install\n_build/\n.merlin" > .gitignore
    echo "# $project_name\n\nAn OCaml project built with Dune." > README.md

    if [ ! -f "${project_name}.opam" ]; then
        cat > "${project_name}.opam" << EOF
opam-version: "2.0"
name: "$project_name"
version: "0.1.0"
synopsis: "A new OCaml project"
description: "A longer description"
maintainer: ["Matt A. Porter <map@qompass.ai>"]
authors: ["Matt A. Porter <map@qompass.ai>"]
depends: [
  "ocaml" {>= "4.14"}
  "dune" {>= "3.0"}
]
build: [
  ["dune" "subst"] {dev}
  ["dune" "build" "-p" name "-j" jobs]
]
EOF
    fi

    echo "Created OCaml project: $project_name"
    echo "Run 'cd $project_name && dune build' to build"
}
ocamlversions() {
    echo "=== OCaml Ecosystem Versions ==="
    command -v ocaml >/dev/null && echo "OCaml: $(ocaml -version)"
    command -v opam >/dev/null && echo "OPAM: $(opam --version)"
    command -v dune >/dev/null && echo "Dune: $(dune --version)"
    command -v utop >/dev/null && echo "UTop: $(utop -version)"
    command -v ocamlformat >/dev/null && echo "OCamlformat: $(ocamlformat --version)"
    command -v ocamllsp >/dev/null && echo "OCaml LSP: $(ocamllsp --version 2>/dev/null || echo 'Available')"
    echo ""
    if command -v opam >/dev/null; then
        echo "Current OPAM switch:"
        opam switch show
        echo ""
        echo "Installed packages:"
        opam list --installed --short | head -10
        [ "$(opam list --installed --short | wc -l)" -gt 10 ] && echo "... and more"
    fi
}
ocamlswitch() {
    local switch_name="${1:-default}"
    local ocaml_version="${2:-4.14.1}"

    echo "Creating OPAM switch '$switch_name' with OCaml $ocaml_version..."
    opam switch create "$switch_name" "$ocaml_version"

    echo "Installing essential packages..."
    opam install -y dune utop ocamlformat ocaml-lsp-server merlin

    echo "Switch '$switch_name' created and configured."
    echo "Run 'opam switch $switch_name' to activate it."
}
ocamlclean() {
    echo "Cleaning OCaml build artifacts..."
    find . -name "_build" -type d -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.install" -delete 2>/dev/null || true
    find . -name ".merlin" -delete 2>/dev/null || true
    dune clean 2>/dev/null || true
    echo "OCaml cleanup completed."
}

ocamlformat_all() {
    echo "Formatting all OCaml files..."
    find . -name "*.ml" -o -name "*.mli" | while read -r file; do
        echo "Formatting: $file"
        ocamlformat --inplace "$file"
    done
    echo "OCaml formatting completed."
}
export -f ocamlproject ocamlversions ocamlswitch ocamlclean ocamlformat_all
