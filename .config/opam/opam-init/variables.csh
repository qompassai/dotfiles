# Prefix of the current opam switch
if ( ! ${?OPAM_SWITCH_PREFIX} ) setenv OPAM_SWITCH_PREFIX ""
setenv OPAM_SWITCH_PREFIX '/home/phaedrus/.opam/squirrel-prover-git'
# Updated by package ocaml-compiler
if ( ! ${?CAML_LD_LIBRARY_PATH} ) setenv CAML_LD_LIBRARY_PATH ""
setenv CAML_LD_LIBRARY_PATH '/home/phaedrus/.opam/squirrel-prover-git/lib/stublibs'
# Updated by package ocaml
if ( ! ${?OCAMLTOP_INCLUDE_PATH} ) setenv OCAMLTOP_INCLUDE_PATH ""
setenv OCAMLTOP_INCLUDE_PATH '/home/phaedrus/.opam/squirrel-prover-git/lib/toplevel':"$OCAMLTOP_INCLUDE_PATH"
# Updated by package ocaml
if ( ! ${?CAML_LD_LIBRARY_PATH} ) setenv CAML_LD_LIBRARY_PATH ""
setenv CAML_LD_LIBRARY_PATH '/home/phaedrus/.opam/squirrel-prover-git/lib/ocaml/stublibs:/home/phaedrus/.opam/squirrel-prover-git/lib/ocaml'
# Updated by package ocaml
if ( ! ${?CAML_LD_LIBRARY_PATH} ) setenv CAML_LD_LIBRARY_PATH ""
setenv CAML_LD_LIBRARY_PATH '/home/phaedrus/.opam/squirrel-prover-git/lib/stublibs':"$CAML_LD_LIBRARY_PATH"
# Updated by package ocaml
if ( ! ${?OCAML_TOPLEVEL_PATH} ) setenv OCAML_TOPLEVEL_PATH ""
setenv OCAML_TOPLEVEL_PATH '/home/phaedrus/.opam/squirrel-prover-git/lib/toplevel'
# Current opam switch man dir
if ( ! ${?MANPATH} ) setenv MANPATH ""
setenv MANPATH "$MANPATH":'/home/phaedrus/.opam/squirrel-prover-git/man'
# Binary dir for opam switch squirrel-prover-git
if ( ! ${?PATH} ) setenv PATH ""
setenv PATH '/home/phaedrus/.opam/squirrel-prover-git/bin':"$PATH"
