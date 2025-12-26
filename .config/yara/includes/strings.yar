// /qompassai/dotfiles/.config/yara/includes/strings.yar
// Qompass AI Yara Strings
// Copyright (C) 2025 Qompass AI, All rights reserved
// ----------------------------------------

import "pe"

rule Common_Suspicious_Strings
{
    meta:
        author = "Qompass AI"
        description = "Common suspicious string patterns"
        reference = "Internal baseline"

    strings:
        $cmd_exe  = "cmd.exe" nocase
        $powershell = "powershell.exe" nocase
        $wget     = "wget " nocase
        $curl     = "curl " nocase

    condition:
        any of ($cmd_exe, $powershell, $wget, $curl)
}

