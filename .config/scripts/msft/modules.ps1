#!/usr/bin/env pwsh
$modules = @(
    # A
    "Az",
    "AWS.Tools.Installer",
    "ArcGIS",
    "dbatools",
    "DSInternals",
    "ImportExcel",
    "InvokeBuild",
    "Microsoft.PowerApps.Administration.PowerShell",
    "Microsoft.PowerApps.PowerShell",
    "Microsoft.PowerShell.SecretManagement",
    "Microsoft.PowerShell.SecretStore",
    "Microsoft.PowerShell.UnixCompleters",
    "MicrosoftTeams",
    "NTFSSecurity",
    "Pester",
    "Plaster",
    "PlatyPS",
    "posh-git",
    "PowerShellGet",
    "powershell-yaml",
    "PowerShellAI",
    "PSReadLine",
    "PSWriteHTML",
    "Terminal-Icons"
)
foreach ($module in $modules) {
    if (-not (Get-Module -ListAvailable -Name $module)) {
        Write-Host "Installing $module..." -ForegroundColor Cyan
        Install-Module -Name $module -Scope CurrentUser -AllowClobber -Force
        Write-Host "$module installed." -ForegroundColor Green
    } else {
        Write-Host "$module already installed, skipping." -ForegroundColor Yellow
    }
}
Write-Host "`nInstalling Power Platform CLI (pac)..." -ForegroundColor Cyan
if (Get-Command dotnet -ErrorAction SilentlyContinue) {
    dotnet tool install --global Microsoft.PowerApps.CLI.Tool
    Write-Host "pac installed." -ForegroundColor Green
} else {
    Write-Host "dotnet not found — skipping pac. Install .NET SDK: https://dotnet.microsoft.com/download" -ForegroundColor Red
}
Write-Host "`nInstalling AWS Tools submodules..." -ForegroundColor Cyan
if (Get-Module -ListAvailable -Name AWS.Tools.Installer) {
    Import-Module AWS.Tools.Installer
    Install-AWSToolsModule S3, EC2, IAM -CleanUp -Force
    Write-Host "AWS submodules installed." -ForegroundColor Green
} else {
    Write-Host "AWS.Tools.Installer not found, skipping AWS submodules." -ForegroundColor Red
}
if (Get-Module -ListAvailable -Name PowerShellAI) {
    if (-not $env:OPENAI_API_KEY) {
        Write-Host "`nPowerShellAI installed. Set your OpenAI API key to enable Copilot:" -ForegroundColor Yellow
        Write-Host '  $env:OPENAI_API_KEY = "sk-..."' -ForegroundColor White
        Write-Host '  Set-OpenAIKey' -ForegroundColor White
    }
}
Write-Host "`nAll modules processed." -ForegroundColor Magenta
