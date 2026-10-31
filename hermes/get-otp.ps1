<#
.SYNOPSIS
    Mochi Host OTP Generator for Windows
.DESCRIPTION
    Generates a 6-digit TOTP (RFC 6238) for authenticating Hermes with the host machine.
#>

param(
    [switch]$Loop,
    [switch]$ShowUri
)

$secret = "4UNGXTOTY3FHZ45MIKOP7HSBUJS73WGQ"
$secretFile = Join-Path $PSScriptRoot ".totp_secret"
if (Test-Path $secretFile) {
    $fileSecret = (Get-Content $secretFile -Raw).Trim()
    if ($fileSecret) { $secret = $fileSecret }
}

function Get-TotpCode {
    param([string]$Base32Secret)
    
    $base32Chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"
    $cleanSecret = $Base32Secret.ToUpper().Replace(" ", "").Replace("=", "")
    $bits = ""
    foreach ($c in $cleanSecret.ToCharArray()) {
        $val = $base32Chars.IndexOf($c)
        if ($val -ge 0) {
            $bits += [Convert]::ToString($val, 2).PadLeft(5, '0')
        }
    }
    $byteCount = [Math]::Floor($bits.Length / 8)
    $keyBytes = New-Object byte[] $byteCount
    for ($i = 0; $i -lt $byteCount; $i++) {
        $keyBytes[$i] = [Convert]::ToByte($bits.Substring($i * 8, 8), 2)
    }

    $unixTime = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
    $step = [Math]::Floor($unixTime / 30)
    $timeBytes = [BitConverter]::GetBytes([long]$step)
    if ([BitConverter]::IsLittleEndian) {
        [Array]::Reverse($timeBytes)
    }

    $hmac = New-Object System.Security.Cryptography.HMACSHA1
    $hmac.Key = $keyBytes
    $hash = $hmac.ComputeHash($timeBytes)

    $offset = $hash[$hash.Length - 1] -band 0x0F
    $codeInt = (($hash[$offset] -band 0x7F) -shl 24) -bor `
               (($hash[$offset + 1] -band 0xFF) -shl 16) -bor `
               (($hash[$offset + 2] -band 0xFF) -shl 8) -bor `
               ($hash[$offset + 3] -band 0xFF)
    
    $code = ($codeInt % 1000000).ToString("D6")
    $remaining = 30 - ($unixTime % 30)
    return @{ Code = $code; Remaining = $remaining }
}

$otpAuthUri = "otpauth://totp/Mochi:Conde?secret=$secret&issuer=MochiBot"

if ($ShowUri) {
    Write-Host "`nAuthenticator URI (for Google Authenticator / 1Password):" -ForegroundColor Cyan
    Write-Host $otpAuthUri -ForegroundColor Yellow
    Write-Host "Secret Key: $secret`n" -ForegroundColor Gray
    exit 0
}

function Show-Otp {
    $res = Get-TotpCode -Base32Secret $secret
    try {
        Set-Clipboard -Value $res.Code -ErrorAction SilentlyContinue
        $copied = " [Copied to clipboard!]"
    } catch {
        $copied = ""
    }

    Write-Host ""
    Write-Host "==========================================================" -ForegroundColor Magenta
    Write-Host "         Mochi Host OTP Generator (Conde PC)              " -ForegroundColor Cyan
    Write-Host "==========================================================" -ForegroundColor Magenta
    Write-Host "  Current OTP Code : " -NoNewline -ForegroundColor White
    Write-Host "$($res.Code)" -NoNewline -ForegroundColor Green -BackgroundColor Black
    Write-Host "$copied" -ForegroundColor Gray
    Write-Host "  Valid Remaining  : $($res.Remaining) seconds" -ForegroundColor Yellow
    Write-Host "==========================================================" -ForegroundColor Magenta
    Write-Host "Tip: Scan to phone: .\get-otp.ps1 -ShowUri" -ForegroundColor DarkGray
    Write-Host ""
}

Show-Otp

if ($Loop) {
    while ($true) {
        Start-Sleep -Seconds 1
        $now = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
        if (($now % 30) -eq 0) {
            Clear-Host
            Show-Otp
        }
    }
}
