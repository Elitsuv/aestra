Write-Host ""
Write-Host "  +-------------------------------------------------------------+" -ForegroundColor Cyan
Write-Host "  |  AESTRA  *  Competitive Programming Execution Sandbox      |" -ForegroundColor Cyan
Write-Host "  +-------------------------------------------------------------+" -ForegroundColor Cyan
Write-Host ""

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
}
if (-not $pythonCmd) {
    $pythonCmd = Get-Command py -ErrorAction SilentlyContinue
}

if (-not $pythonCmd) {
    Write-Host "  [X] Python could not be found." -ForegroundColor Red
    Write-Host "      Please install Python 3.10+ from https://www.python.org or Microsoft Store."
    exit 1
}

$pyVersion = & $pythonCmd.Source -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
Write-Host "  [OK] Python $pyVersion detected" -ForegroundColor Green

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
            Write-Host "  [*] Downloading Aestra archive..." -ForegroundColor Cyan
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
}

$binDir = Join-Path $installDir "bin"
if (-not (Test-Path $binDir)) {
    New-Item -ItemType Directory -Force -Path $binDir | Out-Null
}

$batContent = "@echo off`r`nset PYTHONPATH=$repoRoot;%PYTHONPATH%`r`npython -m src.cli %*"
Set-Content -Path (Join-Path $binDir "aestra.bat") -Value $batContent -Encoding Ascii
Set-Content -Path (Join-Path $binDir "aestra.cmd") -Value $batContent -Encoding Ascii
Set-Content -Path (Join-Path $repoRoot "aestra.bat") -Value $batContent -Encoding Ascii
Set-Content -Path (Join-Path (Get-Location).Path "aestra.bat") -Value $batContent -Encoding Ascii

$pyScriptsDir = Join-Path (Split-Path $pythonCmd.Source) "Scripts"
if (Test-Path $pyScriptsDir) {
    Set-Content -Path (Join-Path $pyScriptsDir "aestra.bat") -Value $batContent -Encoding Ascii
    Set-Content -Path (Join-Path $pyScriptsDir "aestra.cmd") -Value $batContent -Encoding Ascii
}

$hasCargo = Get-Command cargo -ErrorAction SilentlyContinue
if ($hasCargo) {
    Write-Host "  [OK] Rust toolchain detected - Building native core..." -ForegroundColor Green
    try {
        & $pythonCmd.Source -m pip install --quiet --upgrade maturin
        & $pythonCmd.Source -m maturin develop --release --manifest-path (Join-Path $repoRoot "Cargo.toml") 2>$null
    } catch {
        Write-Host "  [!] Native compilation skipped, falling back to SubprocessEngine." -ForegroundColor Yellow
    }
} else {
    Write-Host "  [OK] SubprocessEngine ready (Zero compiler required on Windows)" -ForegroundColor Green
}

$userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($userPath -notlike "*$binDir*") {
    [Environment]::SetEnvironmentVariable("PATH", "$userPath;$binDir", "User")
}
if ($env:PATH -notlike "*$binDir*") {
    $env:PATH = "$binDir;$env:PATH"
}

Write-Host ""
Write-Host "  +-------------------------------------------------------------+" -ForegroundColor Green
Write-Host "  |  [OK] AESTRA INSTALLED SUCCESSFULLY                         |" -ForegroundColor Green
Write-Host "  +-------------------------------------------------------------+" -ForegroundColor Green
Write-Host "  Location: $repoRoot" -ForegroundColor Gray
Write-Host "  Command : aestra (available globally in PATH)" -ForegroundColor Gray
Write-Host ""
Write-Host "  Quickstart:" -ForegroundColor Yellow
Write-Host "    aestra --help" -ForegroundColor Cyan
Write-Host "    aestra run ./solution.exe --time-limit 1000" -ForegroundColor Cyan
Write-Host "    aestra test ./solution.exe --cases ./testcases/" -ForegroundColor Cyan
Write-Host ""
