@echo off
setlocal
title Aestra Uninstaller

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Get-ChildItem -LiteralPath '%~dp0' -Recurse | Unblock-File -ErrorAction SilentlyContinue" 2>nul

if "%1"=="--cli" goto cli_mode
if "%1"=="-c" goto cli_mode

if exist "%~dp0scripts\uninstall.ps1" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\uninstall.ps1" -Gui
    exit /b 0
)

:cli_mode
if exist "%~dp0scripts\uninstall.ps1" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\uninstall.ps1"
) else (
    echo [*] Uninstall script not found.
)
pause
