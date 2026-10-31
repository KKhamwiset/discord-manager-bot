# setup-windows.ps1
# Script สำหรับตั้งค่า Windows PC ให้ Hermes Agent เชื่อมต่อได้แบบอัตโนมัติ
# วิธีใช้: คลิกขวาที่ไฟล์นี้แล้วเลือก "Run with PowerShell" (หรือรันใน PowerShell as Administrator)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   Hermes Windows Host Setup (Admin privileges required)  " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# ตรวจสอบสิทธิ์ Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "[!] กรุณารันสคริปต์นี้ด้วยสิทธิ์ Administrator (คลิกขวา -> Run with PowerShell as Administrator)" -ForegroundColor Red
    Pause
    exit 1
}

# 1. ตรวจสอบ OpenSSH Server
Write-Host "`n[1/5] ตรวจสอบและเริ่มบริการ OpenSSH Server (sshd)..." -ForegroundColor Yellow
$sshd = Get-Service sshd -ErrorAction SilentlyContinue
if (-not $sshd) {
    Write-Host "กำลังติดตั้ง OpenSSH Server..." -ForegroundColor Gray
    Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0 | Out-Null
}
Set-Service -Name sshd -StartupType 'Automatic'
Start-Service sshd
Write-Host "[✓] OpenSSH Server กำลังทำงาน (Running)" -ForegroundColor Green

# 2. ตั้งค่า DefaultShell ไปที่ Git Bash
Write-Host "`n[2/5] ตั้งค่า DefaultShell สำหรับ SSH ไปที่ Git Bash..." -ForegroundColor Yellow
$gitBashPath = "C:\Program Files\Git\bin\bash.exe"
if (Test-Path $gitBashPath) {
    New-ItemProperty -Path "HKLM:\SOFTWARE\OpenSSH" -Name DefaultShell -Value $gitBashPath -PropertyType String -Force | Out-Null
    Write-Host "[✓] ตั้งค่า DefaultShell = $gitBashPath เรียบร้อย" -ForegroundColor Green
} else {
    Write-Host "[!] ไม่พบ Git Bash ที่ $gitBashPath (แนะนำให้ติดตั้ง Git for Windows)" -ForegroundColor Yellow
}

# 3. จัดการ Authorized Keys สำหรับ Administrator User
Write-Host "`n[3/5] ตั้งค่า Public Key ใน administrators_authorized_keys..." -ForegroundColor Yellow
$pubKeyFile = "$HOME\.ssh\id_ed25519.pub"
$adminAuthKeys = "C:\ProgramData\ssh\administrators_authorized_keys"

if (Test-Path $pubKeyFile) {
    $pubKeyContent = (Get-Content $pubKeyFile -Raw).Trim()
    Set-Content -Path $adminAuthKeys -Value $pubKeyContent -Encoding ascii -Force
    
    # กำหนดสิทธิ์ ACL ให้เข้มงวดตามมาตรฐาน OpenSSH
    icacls $adminAuthKeys /inheritance:r /grant "SYSTEM:(F)" /grant "Administrators:(F)" | Out-Null
    Write-Host "[✓] คัดลอก Public Key และกำหนด Permissions ให้ $adminAuthKeys สำเร็จ" -ForegroundColor Green
} else {
    Write-Host "[!] ไม่พบไฟล์ $pubKeyFile กรุณารัน 'ssh-keygen -t ed25519' ก่อน" -ForegroundColor Red
}

# 4. ตรวจสอบและติดตั้ง Tailscale
Write-Host "`n[4/5] ตรวจสอบ Tailscale..." -ForegroundColor Yellow
$tailscaleCmd = Get-Command tailscale -ErrorAction SilentlyContinue
if (-not $tailscaleCmd -and -not (Test-Path "C:\Program Files\Tailscale\tailscale.exe")) {
    Write-Host "กำลังติดตั้ง Tailscale ผ่าน winget..." -ForegroundColor Gray
    winget install --id Tailscale.Tailscale -e --accept-package-agreements --accept-source-agreements --silent
    Write-Host "[✓] ติดตั้ง Tailscale เรียบร้อย กรุณาเปิดโปรแกรม Tailscale แล้ว Login" -ForegroundColor Green
} else {
    Write-Host "[✓] Tailscale ถูกติดตั้งอยู่แล้ว" -ForegroundColor Green
}

# 5. Restart sshd และทดสอบเชื่อมต่อ
Write-Host "`n[5/5] รีสตาร์ท OpenSSH Server และทดสอบ..." -ForegroundColor Yellow
Restart-Service sshd

try {
    $testResult = & ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new "$($env:USERNAME)@localhost" "echo 'SSH_OK'" 2>&1
    if ($testResult -match 'SSH_OK') {
        Write-Host "[✓] ทดสอบเชื่อมต่อ SSH Local สำเร็จ 100%! บัญชีพร้อมรับคำสั่งจาก Hermes แล้ว" -ForegroundColor Green
    } else {
        Write-Host "[!] ผลการทดสอบ: $testResult" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[!] เกิดข้อผิดพลาดในการทดสอบ SSH: $_" -ForegroundColor Red
}

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host "การตั้งค่าเครื่องเสร็จสิ้น! กด Enter เพื่อปิดหน้าต่างนี้" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Pause
