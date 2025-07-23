#!/usr/bin/env sh
# /qompassai/Shell/.profile.d/62-perl.sh
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################

export PATH="$PATH:$HOME/.perl5/bin"
export PERL5LIB="$HOME/.perl5/lib/perl5:$HOME/lib/perl5"
export PERL_CPANM_HOME="$HOME/.cpanm"
export PERL_CPANM_OPT="--local-lib=$HOME/.perl5"
export PERL_LOCAL_LIB_ROOT="$HOME/.perl5"
export PERL_MB_OPT="--install_base $HOME/.perl5"
export PERL_MM_OPT="INSTALL_BASE=$HOME/.perl5"

