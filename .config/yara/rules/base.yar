// /qompassai/dotfiles/.config/yara/rules/base_rules.yar
// Qompass AI Yara Base Rules
// Copyright (C) 2025 Qompass AI, All rights reserved
/////////////////////////////////////////////////////
include "../includes/common_strings.yar"
rule Suspicious_Executable_With_Cmd
{
    meta:
        author = "Qompass AI"
        description = "PE file that imports WinExec and contains cmd.exe"
        severity = "medium"

    strings:
        $cmd = "cmd.exe" nocase

    condition:
        pe.is_pe and
        pe.imports("KERNEL32.DLL", "WinExec") and
        $cmd
}
