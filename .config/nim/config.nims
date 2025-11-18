# /qompassai/dotfiles/.config/nim/config.nims
# Qompass AI Nims Config
# Copyright (C) 2025 Qompass AI, All rights reserved
####################################################
cppDefine "errno"
cppDefine "unix"
cppDefine "NAN_INFINITY"
cppDefine "INF"
cppDefine "NAN"

when defined(nimStrictMode):
  when defined(nimHasWarningAsError):
    switch("warningAsError", "UnusedImport")
  when defined(nimHasHintAsError):
    switch("hint", "ConvFromXtoItselfNotNeeded")
  switch("hintAsError", "ConvFromXtoItselfNotNeeded")
  # future work: XDeclaredButNotUsed

switch("define", "nimVersion:" & NimVersion)

