@echo off
setlocal
title Aestra v1.0.1 Setup Wizard

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Get-ChildItem -LiteralPath '%~dp0' -Recurse | Unblock-File -ErrorAction SilentlyContinue" 2>nul

if "%1"=="--cli" goto cli_mode
if "%1"=="-c" goto cli_mode

if exist "%~dp0scripts\wizard.ps1" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\wizard.ps1"
    exit /b 0
)

:cli_mode
cls
echo ============================================================
echo   AESTRA v1.0.1 Windows Setup Wizard (Console Mode)
echo   Deterministic CP Execution Sandbox
echo ============================================================
echo.

if exist "%~dp0scripts\install.ps1" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install.ps1"
) else (
    echo [*] Downloading latest installer script...
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Invoke-Expression (Invoke-RestMethod 'https://raw.githubusercontent.com/Elitsuv/aestra/main/scripts/install.ps1')"
)

pause
