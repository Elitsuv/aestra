[CmdletBinding()]
param(
    [string]$OutDir = "dist",
    [string]$Version = "1.1.1"
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$cleanVersion = $Version.TrimStart('v')

Write-Host "`n  [+] Aestra MSI Installer Build System" -ForegroundColor Cyan
Write-Host "      Target Version: v$cleanVersion" -ForegroundColor Gray
Write-Host "      Repository Root: $repoRoot" -ForegroundColor Gray

$targetOutDir = if ([System.IO.Path]::IsPathRooted($OutDir)) { $OutDir } else { Join-Path $repoRoot $OutDir }
if (-not (Test-Path $targetOutDir)) {
    New-Item -ItemType Directory -Force -Path $targetOutDir | Out-Null
}

$wixCmd = Get-Command wix -ErrorAction SilentlyContinue

if (-not $wixCmd) {
    Write-Host "  [*] WiX v4+ was not found on PATH. Attempting dotnet tool lookup..." -ForegroundColor Yellow
    $dotnetCmd = Get-Command dotnet -ErrorAction SilentlyContinue
    if ($dotnetCmd) {
        Write-Host "  [*] Installing WiX CLI via dotnet tool..." -ForegroundColor Cyan
        & dotnet tool install --global wix --version 4.* -ErrorAction SilentlyContinue
        $wixCmd = Get-Command wix -ErrorAction SilentlyContinue
    }
}

if (-not $wixCmd) {
    Write-Host "`n  [!] WiX Toolset is required to build the native MSI installer." -ForegroundColor Red
    Write-Host "      Install WiX on Windows via:" -ForegroundColor Yellow
    Write-Host "      dotnet tool install --global wix`n" -ForegroundColor Cyan
    exit 1
}

$msiVersioned = Join-Path $targetOutDir "Aestra-Setup-$cleanVersion.msi"
$msiGeneric = Join-Path $targetOutDir "Aestra-Setup.msi"
$wxsPath = Join-Path $scriptDir "aestra.wxs"

Write-Host "  [*] Compiling MSI package: $msiVersioned..." -ForegroundColor Cyan
Push-Location $repoRoot
try {
    & wix build $wxsPath -o $msiVersioned
} finally {
    Pop-Location
}

if (Test-Path $msiVersioned) {
    Copy-Item -Path $msiVersioned -Destination $msiGeneric -Force
    $size = (Get-Item $msiVersioned).Length / 1KB
    Write-Host "  [OK] Successfully generated:" -ForegroundColor Green
    Write-Host "       - $msiVersioned ($([math]::Round($size, 1)) KB)" -ForegroundColor Green
    Write-Host "       - $msiGeneric" -ForegroundColor Green
} else {
    Write-Host "  [X] Failed to generate MSI package." -ForegroundColor Red
    exit 1
}
