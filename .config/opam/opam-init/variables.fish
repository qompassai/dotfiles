# Prefix of the current opam switch
set -gx OPAM_SWITCH_PREFIX '/home/phaedrus/.opam/squirrel-prover-git';
# Updated by package ocaml-compiler
set -gx CAML_LD_LIBRARY_PATH '/home/phaedrus/.opam/squirrel-prover-git/lib/stublibs';
# Updated by package ocaml
set -gx OCAMLTOP_INCLUDE_PATH '/home/phaedrus/.opam/squirrel-prover-git/lib/toplevel':"$OCAMLTOP_INCLUDE_PATH";
# Updated by package ocaml
set -gx CAML_LD_LIBRARY_PATH '/home/phaedrus/.opam/squirrel-prover-git/lib/ocaml/stublibs:/home/phaedrus/.opam/squirrel-prover-git/lib/ocaml';
# Updated by package ocaml
set -gx CAML_LD_LIBRARY_PATH '/home/phaedrus/.opam/squirrel-prover-git/lib/stublibs':"$CAML_LD_LIBRARY_PATH";
# Updated by package ocaml
set -gx OCAML_TOPLEVEL_PATH '/home/phaedrus/.opam/squirrel-prover-git/lib/toplevel';
# Current opam switch man dir
if [ (count $MANPATH) -gt 0 ]; set -gx MANPATH $MANPATH '/home/phaedrus/.opam/squirrel-prover-git/man'; end;
# Binary dir for opam switch squirrel-prover-git
set -gx PATH '/home/phaedrus/.opam/squirrel-prover-git/bin' $PATH;
