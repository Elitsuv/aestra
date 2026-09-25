@echo off
setlocal
title Aestra v1.0.0 Setup Wizard

:: If run with --cli or -c, run console mode
if "%1"=="--cli" goto cli_mode
if "%1"=="-c" goto cli_mode

:: Launch graphical Wizard Window by default
if exist "%~dp0scripts\wizard.ps1" (
    start "" powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0scripts\wizard.ps1"
    exit /b 0
)

:cli_mode
cls
echo ============================================================
echo   AESTRA v1.0.0 Windows Setup Wizard (Console Mode)
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
