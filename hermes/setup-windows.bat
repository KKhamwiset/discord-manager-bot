@echo off
setlocal
title Hermes Windows Host Setup

echo Requesting Administrator privileges...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process powershell.exe -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"\"%~dp0setup-windows.ps1\"\"' -Verb RunAs"

exit /b

