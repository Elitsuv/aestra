Write-Host ""
Write-Host "  +-------------------------------------------------------------+" -ForegroundColor Cyan
Write-Host "  |  AESTRA SETUP WIZARD  *  v1.0.0 Stable Launch (Windows)    |" -ForegroundColor Cyan
Write-Host "  |  Deterministic CP Execution Sandbox & Microsecond Telemetry |" -ForegroundColor Cyan
Write-Host "  +-------------------------------------------------------------+" -ForegroundColor Cyan
Write-Host ""

# 1. Detect Python
Write-Host "  [Step 1/5] Checking Python environment..." -ForegroundColor White
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) { $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $pythonCmd) { $pythonCmd = Get-Command py -ErrorAction SilentlyContinue }

if (-not $pythonCmd) {
    Write-Host "  [X] Python 3.10+ was not found on your system." -ForegroundColor Red
    Write-Host "      Please install Python from https://www.python.org or run:" -ForegroundColor Yellow
    Write-Host "      winget install Python.Python.3.12" -ForegroundColor Cyan
    exit 1
}

$pyVersion = & $pythonCmd.Source -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
Write-Host "  [OK] Python $pyVersion detected ($($pythonCmd.Source))" -ForegroundColor Green

# 2. Determine target install directory
Write-Host "`n  [Step 2/5] Setting up Aestra core files..." -ForegroundColor White
$installDir = Join-Path $HOME ".aestra"
$isLocalRepo = (Test-Path "pyproject.toml") -and (Test-Path "src")

if (-not $isLocalRepo) {
    if (Test-Path (Join-Path $installDir ".git")) {
        Write-Host "  [*] Updating Aestra in $installDir..." -ForegroundColor Cyan
        & git -C $installDir pull --quiet
    } else {
        if (Test-Path $installDir) {
            Remove-Item -Recurse -Force $installDir -ErrorAction SilentlyContinue
        }
        $hasGit = Get-Command git -ErrorAction SilentlyContinue
        if ($hasGit) {
            Write-Host "  [*] Cloning Aestra repository into $installDir..." -ForegroundColor Cyan
            & git clone --depth 1 --quiet "https://github.com/Elitsuv/aestra.git" $installDir
        } else {
            Write-Host "  [*] Downloading Aestra distribution archive..." -ForegroundColor Cyan
            $zipPath = "$installDir.zip"
            Invoke-WebRequest -Uri "https://github.com/Elitsuv/aestra/archive/refs/heads/main.zip" -OutFile $zipPath
            Expand-Archive -Path $zipPath -DestinationPath $HOME -Force
            if (Test-Path (Join-Path $HOME "aestra-main")) {
                Rename-Item (Join-Path $HOME "aestra-main") ".aestra" -Force
            }
            Remove-Item $zipPath -Force
        }
    }
    $repoRoot = $installDir
} else {
    $repoRoot = (Get-Location).Path
    $srcSource = Join-Path $repoRoot "src"
    $srcDest = Join-Path $installDir "src"
    if (Test-Path $srcSource) {
        Copy-Item -Path $srcSource -Destination $srcDest -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# 3. Create execution shims & binary directory
Write-Host "`n  [Step 3/5] Creating global CLI launcher..." -ForegroundColor White
$binDir = Join-Path $installDir "bin"
if (-not (Test-Path $binDir)) {
    New-Item -ItemType Directory -Force -Path $binDir | Out-Null
}

$batContent = "@echo off`r`nset PYTHONPATH=$installDir;%PYTHONPATH%`r`npython -m src.cli %*"
Set-Content -Path (Join-Path $binDir "aestra.bat") -Value $batContent -Encoding Ascii
Set-Content -Path (Join-Path $binDir "aestra.cmd") -Value $batContent -Encoding Ascii
Set-Content -Path (Join-Path $repoRoot "aestra.bat") -Value $batContent -Encoding Ascii

# Also register in Python Scripts directory if accessible
$pyScriptsDir = Join-Path (Split-Path $pythonCmd.Source) "Scripts"
if (Test-Path $pyScriptsDir) {
    Set-Content -Path (Join-Path $pyScriptsDir "aestra.bat") -Value $batContent -Encoding Ascii
    Set-Content -Path (Join-Path $pyScriptsDir "aestra.cmd") -Value $batContent -Encoding Ascii
}

# 4. Install App Icon and Desktop Shortcut
Write-Host "`n  [Step 4/5] Configuring App Icon and Shortcuts..." -ForegroundColor White
$assetsTarget = Join-Path $installDir "assets"
if (-not (Test-Path $assetsTarget)) {
    New-Item -ItemType Directory -Force -Path $assetsTarget | Out-Null
}

$localIco = Join-Path $repoRoot "assets\aestra.ico"
$targetIco = Join-Path $assetsTarget "aestra.ico"
if (Test-Path $localIco) {
    Copy-Item $localIco $targetIco -Force -ErrorAction SilentlyContinue
}

try {
    $wshShell = New-Object -ComObject WScript.Shell
    $desktopPath = [Environment]::GetFolderPath("Desktop")
    $shortcutPath = Join-Path $desktopPath "Aestra.lnk"
    $shortcut = $wshShell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = (Join-Path $binDir "aestra.bat")
    $shortcut.WorkingDirectory = $HOME
    $shortcut.Description = "Aestra - Deterministic CP Execution Sandbox"
    if (Test-Path $targetIco) {
        $shortcut.IconLocation = "$targetIco,0"
    }
    $shortcut.Save()
    Write-Host "  [OK] Desktop shortcut created with Aestra App Icon" -ForegroundColor Green
} catch {
    Write-Host "  [!] Desktop shortcut creation skipped (non-critical)" -ForegroundColor Yellow
}

# 5. Permanent PATH registration
Write-Host "`n  [Step 5/5] Registering global PATH variable..." -ForegroundColor White
$userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($userPath -notlike "*$binDir*") {
    [Environment]::SetEnvironmentVariable("PATH", "$userPath;$binDir", "User")
    Write-Host "  [OK] Added $binDir to User PATH permanently" -ForegroundColor Green
}
if ($env:PATH -notlike "*$binDir*") {
    $env:PATH = "$binDir;$env:PATH"
}

Write-Host ""
Write-Host "  +-------------------------------------------------------------+" -ForegroundColor Green
Write-Host "  |  [OK] AESTRA v1.0.0 INSTALLED SUCCESSFULLY                  |" -ForegroundColor Green
Write-Host "  +-------------------------------------------------------------+" -ForegroundColor Green
Write-Host "  Installation Path : $repoRoot" -ForegroundColor Gray
Write-Host "  Global Command    : aestra (Available in any terminal)" -ForegroundColor Gray
Write-Host "  Desktop App       : Aestra icon created on your Desktop" -ForegroundColor Gray
Write-Host ""
Write-Host "  How to use:" -ForegroundColor Yellow
Write-Host "    Open any terminal and simply type: aestra" -ForegroundColor Cyan
Write-Host "    Or run batch tests: aestra test solution.cpp --cases ./cases" -ForegroundColor Cyan
Write-Host "    Or check toolchains: aestra doctor" -ForegroundColor Cyan
Write-Host ""
