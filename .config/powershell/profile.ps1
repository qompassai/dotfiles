# profile.ps1
# Qompass AI - [Add description here]
# Copyright (C) 2025 Qompass AI, All rights reserved
# ----------------------------------------
# ~/.config/powershell/profile.ps1

Import-Module PSReadLine
Set-PSReadLineOption -HistorySaveStyle SaveIncrementally
Set-PSReadLineOption -PredictionSource History

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# Load custom modules if present
$script:ModulePath = [Environment]::GetFolderPath("MyDocuments") + "/PowerShell/Modules"
if (Test-Path $ModulePath) {
    Get-ChildItem $ModulePath -Directory | ForEach-Object {
        Import-Module $_.FullName -ErrorAction SilentlyContinue
    }
}

# Aliases for remote administration
Set-Alias ssh Enter-PSSession
Set-Alias scp Copy-Item
Set-Alias sftp Copy-Item

# WinRM configuration function (for reference)
function Enable-RemoteWinRM {
    Invoke-Command -ScriptBlock {
        Enable-PSRemoting -Force
        Set-Item WSMan:\localhost\Client\TrustedHosts -Value '*'
        # Open firewall ports
        New-NetFirewallRule -Name "WinRM TCP" -Protocol TCP -Port 5985 -Action Allow
    } -ComputerName $args[0] -Credential (Get-Credential)
}

# Connect to remote Windows host with credentials
function Connect-Windows {
    param(
        [Parameter(Mandatory)]
        [string]$ComputerName,
        [Parameter()]
        [string]$User = $env:USER
    )
    $cred = Get-Credential -UserName $User -Message "Enter password for $User"
    Enter-PSSession -ComputerName $ComputerName -Credential $cred
}

# Copy file to remote host
function Copy-ToWindows {
    param(
        [Parameter(Mandatory)]
        [string]$ComputerName,
        [Parameter(Mandatory)]
        [string]$LocalPath,
        [Parameter(Mandatory)]
        [string]$RemotePath,
        [Parameter()]
        [string]$User = $env:USER
    )
    $cred = Get-Credential -UserName $User
    Copy-Item $LocalPath -Destination "\\$ComputerName\$RemotePath" -Credential $cred
}

# Gather remote system info
function Get-RemoteSystemInfo {
    param(
        [Parameter(Mandatory)]
        [string]$ComputerName,
        [Parameter()]
        [string]$User = $env:USER
    )
    $cred = Get-Credential -UserName $User
    Invoke-Command -ComputerName $ComputerName -Credential $cred -ScriptBlock {
        Get-ComputerInfo
        Get-Service | Where-Object {$_.Status -eq "Running"}
        Get-Process | Sort-Object CPU -Descending | Select-Object -First 10
    }
}

# Helpful network info from Linux side
function Get-NetInfo {
    ip addr show
    ip route show
    nmap -sn <your subnet here>
}

# Export/Import SSH keys for passwordless access (if ssh enabled on Windows)
function Export-SSHKey {
    # Usage: Export-SSHKey -User <WindowsUser> -ComputerName <WindowsHost>
    param (
        [Parameter(Mandatory)]
        [string]$User,
        [Parameter(Mandatory)]
        [string]$ComputerName
    )
    ssh-copy-id $User@$ComputerName
}

Write-Host "💻 PowerShell profile loaded. Ready for remote Windows work." -ForegroundColor Cyan

