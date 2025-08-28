# go.fish
# Qompass AI Go Fish Config
# Copyright (C) 2025 Qompass AI, All rights reserved
# ----------------------------------------
# Set path to Go installation (adjust if installed elsewhere)
set -gx GOROOT /usr/lib/go

# Set Go workspace (change this to your Go workspace directory)
set -gx GOPATH $HOME/go

# Add Go bin directories to PATH
set -gx PATH $GOROOT/bin $GOPATH/bin $PATH

