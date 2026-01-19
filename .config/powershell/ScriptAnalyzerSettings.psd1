# ScriptAnalyzerSettings.psd1
# Qompass AI Powershell ScriptAnalyzerSettings
# Copyright (C) 2025 Qompass AI, All rights reserved
# ----------------------------------------
@{
    Severity = @{
        "PSAvoidUsingPlainTextForSecret"         = "Warning"
        "PSAvoidUsingDeprecatedManifestFields"   = "Warning"
        "PSAvoidUsingWriteHost"                  = "Hint"
        "PSAvoidGlobalVars"                      = "Warning"
        "PSUseConsistentIndentation"             = "Information"
        "PSUseConsistentWhitespace"              = "Information"
        "PSAvoidUsingBrokenHashAlgorithms"       = "Error"
        "PSUseCorrectCasing"                     = "Warning"
        "PSAvoidUsingEmptyCatchBlock"            = "Warning"
        "PSAvoidUsingUserNameAndPasswordParams"  = "Warning"
        "PSUseDeclaredVarsMoreThanAssignments"   = "Hint"
        "PSAvoidTrailingWhitespace"              = "Information"
        "PSUseToExportFromManifest"              = "Warning"
    }

    ExcludeRules = @(
        "PSUseApprovedVerbs"
        "PSShouldProcess"
    )

    IncludeRules = @(
        "PSAvoidUsingPlainTextForSecret"
        "PSAvoidUsingWriteHost"
        "PSAvoidUsingDeprecatedManifestFields"
        "PSUseCorrectCasing"
    )

    CustomRuleParameters = @{
        "PSUseConsistentIndentation" = @{
            "IndentationSize" = 2
            "Kind"           = "space"
        }
    }

    TelemetryEnabled = $false
}

