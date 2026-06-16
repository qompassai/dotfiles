# profile.ps1
# Qompass AI PowerShell Profile
# Copyright (C) 2025 Qompass AI, All rights reserved
# ----------------------------------------
Import-Module PSReadLine
Set-PSReadLineOption -HistorySaveStyle SaveIncrementally
Set-PSReadLineOption -PredictionSource History
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$script:ModulePath = [Environment]::GetFolderPath("MyDocuments") + "/PowerShell/Modules"
if (Test-Path $ModulePath) {
    Get-ChildItem $ModulePath -Directory | ForEach-Object {
        Import-Module $_.FullName -ErrorAction SilentlyContinue
    }
}
foreach ($name in @('ssh','scp','sftp')) {
    if (Get-Alias $name -ErrorAction SilentlyContinue) {
        Remove-Item "Alias:$name" -ErrorAction SilentlyContinue
    }
}

function Get-WindowsIp {
    (& pass show windows/ip).Trim()
}
function Get-WindowsUser {
    try {
        (& pass show windows/user).Trim()
    } catch {
        $env:USER
    }
}
function Get-WSLUser {
    try {
        (& pass show windows/wsl-user).Trim()
    } catch {
        "phaedrus"
    }
}
function Get-NetInfo {
    param(
        [string]$Subnet = "192.168.0.0/24"
    )
    ip addr show
    ip route show
    if (Get-Command nmap -ErrorAction SilentlyContinue) {
        nmap -sn $Subnet
    } else {
        Write-Warning "nmap is not installed; skipping subnet scan."
    }
}

function Test-WindowsSsh {
    param(
        [string]$HostIp = $(Get-WindowsIp),
        [int]$Port = 22
    )

    ssh -vvv -p $Port "$(Get-WindowsUser)@$HostIp"
}

function Connect-WindowsSsh {
    param(
        [string]$HostIp = $(Get-WindowsIp),
        [string]$User = $(Get-WindowsUser),
        [int]$Port = 22
    )

    ssh -p $Port "$User@$HostIp"
}

function Connect-WSL2Ssh {
    param(
        [string]$HostIp = $(Get-WindowsIp),
        [string]$User = $(Get-WSLUser),
        [int]$Port = 2342
    )

    ssh -p $Port "$User@$HostIp"
}

function Connect-WSLViaWindows {
    param(
        [string]$HostIp = $(Get-WindowsIp),
        [string]$WindowsUser = $(Get-WindowsUser),
        [string]$Distro = "Arch"
    )

    ssh -t "$WindowsUser@$HostIp" "wsl -d $Distro"
}

function Enable-RemoteWinRM {
    param(
        [Parameter(Mandatory)]
        [string]$ComputerName
    )

    Invoke-Command -ScriptBlock {
        Enable-PSRemoting -Force
        Set-Item WSMan:\localhost\Client\TrustedHosts -Value '*'
        New-NetFirewallRule -Name "WinRM TCP" -Protocol TCP -LocalPort 5985 -Action Allow -ErrorAction SilentlyContinue
    } -ComputerName $ComputerName -Credential (Get-Credential)
}

function Connect-WindowsPS {
    param(
        [string]$ComputerName = $(Get-WindowsIp),
        [string]$User = $(Get-WindowsUser)
    )

    $cred = Get-Credential -UserName $User -Message "Enter password for $User"
    Enter-PSSession -ComputerName $ComputerName -Credential $cred
}

function Copy-ToWindows {
    param(
        [string]$ComputerName = $(Get-WindowsIp),
        [Parameter(Mandatory)]
        [string]$LocalPath,
        [Parameter(Mandatory)]
        [string]$RemotePath,
        [string]$User = $(Get-WindowsUser)
    )

    $dest = "\\$ComputerName\$RemotePath"
    Copy-Item $LocalPath -Destination $dest
}

function Get-RemoteSystemInfo {
    param(
        [string]$ComputerName = $(Get-WindowsIp),
        [string]$User = $(Get-WindowsUser)
    )

    $cred = Get-Credential -UserName $User
    Invoke-Command -ComputerName $ComputerName -Credential $cred -ScriptBlock {
        Get-ComputerInfo
        Get-Service | Where-Object { $_.Status -eq "Running" }
        Get-Process | Sort-Object CPU -Descending | Select-Object -First 10
    }
}

function Export-SSHKey-ToWindows {
    param(
        [string]$HostIp = $(Get-WindowsIp),
        [string]$User = $(Get-WindowsUser),
        [int]$Port = 22
    )

    ssh-copy-id -p $Port "$User@$HostIp"
}

function Export-SSHKey-ToWSL2 {
    param(
        [string]$HostIp = $(Get-WindowsIp),
        [string]$User = $(Get-WSLUser),
        [int]$Port = 2342
    )

    ssh-copy-id -p $Port "$User@$HostIp"
}

Write-Host "PowerShell profile loaded. pass-backed Windows/WSL helpers ready." -ForegroundColor Cyan
