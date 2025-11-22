# /qompassai/dotfiles/.config/fish/conf.d/perl.fish
# Qompass AI Fish Perl Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
set -x PERL_LOCAL_LIB_ROOT $HOME/.perl5
set -x PERL_MB_OPT "--install_base '$HOME/.perl5'"
set -x PERL_MM_OPT "INSTALL_BASE=$HOME/.perl5"
set -x PERL5LIB "$HOME/.perl5/lib/perl5"
set -U fish_user_paths $HOME/.perl5/bin $fish_user_paths
