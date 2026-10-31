# setup-windows.ps1
# Setup script for Hermes Host on Windows

# Auto-elevate to Administrator if not running as Admin
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Requesting Administrator privileges..." -ForegroundColor Yellow
    Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "        Hermes Windows Host Setup (Administrator)         " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. OpenSSH Server Service
Write-Host "`n[1/5] Checking OpenSSH Server (sshd)..." -ForegroundColor Yellow
$sshd = Get-Service sshd -ErrorAction SilentlyContinue
if (-not $sshd) {
    Write-Host "Installing OpenSSH Server..." -ForegroundColor Gray
    Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0 | Out-Null
}
Set-Service -Name sshd -StartupType Automatic
Start-Service sshd
Write-Host "[OK] OpenSSH Server is running and set to Automatic" -ForegroundColor Green

# 2. Set DefaultShell to Git Bash
Write-Host "`n[2/5] Setting DefaultShell to Git Bash..." -ForegroundColor Yellow
$gitBashPath = "C:\Program Files\Git\bin\bash.exe"
if (Test-Path $gitBashPath) {
    New-ItemProperty -Path "HKLM:\SOFTWARE\OpenSSH" -Name DefaultShell -Value $gitBashPath -PropertyType String -Force | Out-Null
    Write-Host "[OK] DefaultShell set to $gitBashPath" -ForegroundColor Green
} else {
    Write-Host "[WARN] Git Bash not found at $gitBashPath" -ForegroundColor Yellow
}

# 3. Setup administrators_authorized_keys using dedicated passphrase-less key
Write-Host "`n[3/5] Setting up SSH authorized keys for Hermes..." -ForegroundColor Yellow
$hermesKey = "$HOME\.ssh\hermes_ed25519"
$pubKeyFile = "$HOME\.ssh\hermes_ed25519.pub"
$adminAuthKeys = "C:\ProgramData\ssh\administrators_authorized_keys"

# Create hermes_ed25519 if not present
if (-not (Test-Path $pubKeyFile)) {
    Write-Host "Generating dedicated passphrase-less key for Hermes..." -ForegroundColor Gray
    & ssh-keygen -t ed25519 -N '""' -f "$hermesKey" -C "hermes-agent"
}

if (Test-Path $pubKeyFile) {
    $pubKeyContent = (Get-Content $pubKeyFile -Raw).Trim()
    Set-Content -Path $adminAuthKeys -Value $pubKeyContent -Encoding ascii -Force
    
    # Configure strict ACL permissions required by OpenSSH
    icacls $adminAuthKeys /inheritance:r /grant "SYSTEM:(F)" /grant "Administrators:(F)" | Out-Null
    Write-Host "[OK] Configured $adminAuthKeys with hermes_ed25519.pub" -ForegroundColor Green
} else {
    Write-Host "[WARN] Public key not found at $pubKeyFile" -ForegroundColor Red
}

# 4. Check and install Tailscale
Write-Host "`n[4/5] Checking Tailscale..." -ForegroundColor Yellow
$tailscaleExe = "C:\Program Files\Tailscale\tailscale.exe"
if (-not (Test-Path $tailscaleExe)) {
    Write-Host "Tailscale not found. Installing via winget..." -ForegroundColor Gray
    winget install --id Tailscale.Tailscale -e --accept-package-agreements --accept-source-agreements --silent
    Write-Host "[OK] Tailscale installed. Please launch Tailscale and log in" -ForegroundColor Green
} else {
    Write-Host "[OK] Tailscale is already installed" -ForegroundColor Green
    & "$tailscaleExe" ip -4
}

# 5. Restart sshd and test local SSH connection
Write-Host "`n[5/5] Restarting sshd and testing connection..." -ForegroundColor Yellow
Restart-Service sshd

try {
    $testResult = & ssh -i "$hermesKey" -o BatchMode=yes -o StrictHostKeyChecking=accept-new "$($env:USERNAME)@localhost" "echo SSH_SUCCESS" 2>&1
    if ($testResult -match "SSH_SUCCESS") {
        Write-Host "[OK] Local SSH test successful! Your PC is ready for Hermes." -ForegroundColor Green
    } else {
        Write-Host "[INFO] SSH test output: $testResult" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[WARN] SSH test exception: $_" -ForegroundColor Red
}

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "Setup finished! You can close this window." -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Read-Host "Press Enter to exit"
