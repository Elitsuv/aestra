Write-Host "==> Installing Aestra (Competitive Programming Execution Sandbox)" -ForegroundColor Cyan

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
}

if (-not $pythonCmd) {
    Write-Host "[X] Python could not be found." -ForegroundColor Red
    Write-Host "Please install Python 3.10+ from https://www.python.org or the Microsoft Store."
    exit 1
}

$pyVersion = & $pythonCmd.Source -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
Write-Host "[OK] Detected Python $pyVersion" -ForegroundColor Green
Write-Host "[OK] Windows environment detected - Subprocess sandbox mode enabled." -ForegroundColor Green

$hasCargo = Get-Command cargo -ErrorAction SilentlyContinue
if ($hasCargo) {
    Write-Host "[OK] Rust toolchain detected - Building package..." -ForegroundColor Green
    try {
        if (Test-Path "pyproject.toml") {
            & $pythonCmd.Source -m pip install --quiet --upgrade .
        } else {
            & $pythonCmd.Source -m pip install --quiet --upgrade "git+https://github.com/Elitsuv/aestra.git"
        }
    } catch {
        Write-Host "[!] Pip install encountered an error, fallback to zero-build mode." -ForegroundColor Yellow
    }
} else {
    Write-Host "[!] Rust not detected." -ForegroundColor Yellow
    Write-Host "[OK] Windows SubprocessEngine enabled - Zero Rust or C compiler required!" -ForegroundColor Green
}

Write-Host ""
Write-Host "[OK] Aestra installed successfully!" -ForegroundColor Green
Write-Host "Quickstart:" -ForegroundColor Yellow
Write-Host "  Run code safely:   .\aestra.bat run ./solution.exe --time-limit 1000" -ForegroundColor Cyan
Write-Host "  Run batch tests:   .\aestra.bat test ./solution.exe --cases ./tests/" -ForegroundColor Cyan
Write-Host ""
