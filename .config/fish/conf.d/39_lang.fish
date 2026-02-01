#!/usr/bin/env fish
# /qompassai/dotfiles/.config/fish/conf.d/haskell.fish
# Qompass AI Catch-All Lang Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
if not set -q XDG_DATA_HOME
    set -gx XDG_DATA_HOME "$HOME/.local/share"
end
set -gx CABAL_DIR $HOME/.cabal
set -gx FPCDIR "$XDG_DATA_HOME/fpc/src"
set -gx FPCTARGET linux
set -gx FPCTARGETCPU x86_64
set -gx PP "$XDG_DATA_HOME/fpc/bin/ppcx64"
fish_add_path $XDG_DATA_HOME/fpc/bin
fish_add_path $HOME/.ghcup/bin
set -gx METALS_JDK_PATH "/usr/lib/jvm/java-25-openjdk/bin"
set -gx METALS_JAVA_OPTS '-XX:MaxHeapFreeRatio=20 -XX:MinHeapFreeRatio=5 -XX:MaxRAMPercentage=25.0'
fish_add_path $XDG_DATA_HOME/kotlin/kotlin-language-server/bin
set -gx LAZARUSDIR "$XDG_DATA_HOME/lazarus"
fish_add_path $HOME/.nimble/bin
if set -q OPAM_SWITCH_PREFIX; and test -d "$OPAM_SWITCH_PREFIX/bin"
    fish_add_path $OPAM_SWITCH_PREFIX/bin
end
if test -r "$HOME/.opam/opam-init/init.fish"
    source "$HOME/.opam/opam-init/init.fish"
end
set -gx PERL_LOCAL_LIB_ROOT $HOME/.perl5
set -gx PERL_MB_OPT "--install_base '$HOME/.perl5'"
set -gx PERL_MM_OPT "INSTALL_BASE=$HOME/.perl5"
set -gx PERL5LIB "$HOME/.perl5/lib/perl5"
fish_add_path $HOME/.perl5/bin
fish_add_path $XDG_DATA_HOME/racket/bin
fish_add_path $XDG_DATA_HOME/gem/ruby/3.4.0/bin
fish_add_path $HOME/.gem/ruby/3.4.0/bin
set -gx TEXDIR "$XDG_DATA_HOME/texlive/2025"
set -gx TEXMFCONFIG "$XDG_CONFIG_HOME/texlive/texmf-config"
set -gx TEXMFHOME "$XDG_DATA_HOME/texmf"
set -gx TEXMFVAR "$XDG_CACHE_HOME/texlive/texmf-var"
set -gx TEXMFLOCAL "$XDG_DATA_HOME/texlive/texmf-local"
set -gx TEXMFSYSCONFIG "$XDG_DATA_HOME/texlive/texmf-sys-config"
set -gx TEXMFSYSVAR "$XDG_DATA_HOME/texlive/texmf-sys-var"
set -gx INFOPATH "$TEXDIR/texmf-dist/doc/info" $INFOPATH
set -gx MANPATH "$TEXDIR/texmf-dist/doc/man" $MANPATH
fish_add_path $TEXDIR/bin/x86_64-linux
