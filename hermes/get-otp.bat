@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0get-otp.ps1" %*
pause
