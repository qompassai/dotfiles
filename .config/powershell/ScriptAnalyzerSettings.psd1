# ScriptAnalyzerSettings.psd1
# Qompass AI Powershell ScriptAnalyzerSettings
# Copyright (C) 2025 Qompass AI, All rights reserved
# ----------------------------------------
@{
    Severity = @(
        'Error'
        'Warning'
        'Information'
    )

    IncludeDefaultRules = $true

    ExcludeRules = @(
        'PSUseApprovedVerbs'
        'PSShouldProcess'
    )

    IncludeRules = @(
        'PSAvoidUsingPlainTextForSecret'
        'PSAvoidUsingWriteHost'
        'PSAvoidUsingDeprecatedManifestFields'
        'PSUseCorrectCasing'
        'PSAvoidUsingBrokenHashAlgorithms'
        'PSAvoidUsingEmptyCatchBlock'
        'PSAvoidUsingUserNameAndPasswordParams'
        'PSUseDeclaredVarsMoreThanAssignments'
        'PSUseToExportFromManifest'
        'PSAvoidLongLines'
        'PSAlignAssignmentStatement'
        'PSUseConsistentIndentation'
        'PSUseConsistentWhitespace'
    )

    Rules = @{
        PSUseConsistentIndentation = @{
            Enable = $true
            Kind = 'space'
            IndentationSize = 2
        }

        PSUseConsistentWhitespace = @{
            Enable = $true
        }

        PSAvoidLongLines = @{
            Enable = $true
            MaximumLineLength = 100
        }

        PSAlignAssignmentStatement = @{
            Enable = $true
            CheckHashtable = $true
        }
    }

    CustomRulePath = @(
        # '/path/to/custom-rules'
    )

    TelemetryEnabled = $false
}
