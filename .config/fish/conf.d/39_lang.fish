# /qompassai/dotfiles/.config/fish/conf.d/haskell.fish
# Qompass AI Catch-All Lang Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
set -gx PATH $HOME/.ghcup/bin $PATH
set -gx CABAL_DIR $HOME/.cabal
if not set -q XDG_DATA_HOME
    set -x XDG_DATA_HOME "$HOME/.local/share"
end
set -x FPCDIR "$XDG_DATA_HOME/fpc/src"
set -x PP "$XDG_DATA_HOME/fpc/bin/ppcx64"
set -x LAZARUSDIR "$XDG_DATA_HOME/lazarus"
set -x FPCTARGET linux
set -x FPCTARGETCPU x86_64
if not contains "$XDG_DATA_HOME/fpc/bin" $PATH
    set -x PATH "$XDG_DATA_HOME/fpc/bin" $PATH
end
set -gx PATH $XDG_DATA_HOME/racket/bin $PATH
set -gx PATH $XDG_DATA_HOME/kotlin/kotlin-language-server/bin $PATH
set -gx PATH $PATH $HOME/.nimble/bin
#-Ux PATH "$XDG_DATA_HOME/tilt/bin" $PATH
set -x TEXDIR "$XDG_DATA_HOME/texlive/2025"
set -x TEXMFCONFIG "$XDG_CONFIG_HOME/texlive/texmf-config"
set -x TEXMFHOME "$XDG_DATA_HOME/texmf"
set -x TEXMFVAR "$XDG_CACHE_HOME/texlive/texmf-var"
set -x TEXMFLOCAL "$XDG_DATA_HOME/texlive/texmf-local"
set -x TEXMFSYSCONFIG "$XDG_DATA_HOME/texlive/texmf-sys-config"
set -x TEXMFSYSVAR "$XDG_DATA_HOME/texlive/texmf-sys-var"
set -x INFOPATH "$TEXDIR/texmf-dist/doc/info" $INFOPATH
set -x PATH "$TEXDIR/bin/x86_64-linux" $PATH
set -x MANPATH "$TEXDIR/texmf-dist/doc/man" $MANPATH
set -U fish_user_paths $OPAM_SWITCH_PREFIX/bin $fish_user_paths
if test -r "$HOME/.opam/opam-init/init.fish"
    source "$HOME/.opam/opam-init/init.fish"
end
set -x PERL_LOCAL_LIB_ROOT $HOME/.perl5
set -x PERL_MB_OPT "--install_base '$HOME/.perl5'"
set -x PERL_MM_OPT "INSTALL_BASE=$HOME/.perl5"
set -x PERL5LIB "$HOME/.perl5/lib/perl5"
set -U fish_user_paths $HOME/.perl5/bin $fish_user_paths
set -gx METALS_JDK_PATH "/usr/lib/jvm/java-25-openjdk/bin" 
set -gx METALS_JAVA_OPTS '-XX:MaxHeapFreeRatio=20 -XX:MinHeapFreeRatio=5 -XX:MaxRAMPercentage=25.0'
set -Ux fish_user_paths $XDG_DATA_HOME/gem/ruby/3.4.0/bin $fish_user_paths
set -gx PATH $HOME/.gem/ruby/3.4.0/bin $PATH
