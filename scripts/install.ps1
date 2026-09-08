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

$pyVersion = & $pythonCmd.Source -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")'
Write-Host "[✓] Detected Python $pyVersion" -ForegroundColor Green
Write-Host "[✓] Windows environment detected — Subprocess sandbox mode enabled." -ForegroundColor Green

Write-Host "==> Installing Aestra package..." -ForegroundColor Cyan

if (Test-Path "pyproject.toml") {
    & $pythonCmd.Source -m pip install --quiet --upgrade .
} else {
    try {
        & $pythonCmd.Source -m pip install --quiet --upgrade aestra
    } catch {
        & $pythonCmd.Source -m pip install --quiet --upgrade "git+https://github.com/Elitsuv/aestra.git"
    }
}

Write-Host ""
Write-Host "[✓] Aestra installed successfully!" -ForegroundColor Green
Write-Host "Quickstart:" -ForegroundColor Yellow
Write-Host "  Run code safely:   aestra run ./solution.exe --time-limit 1000" -ForegroundColor Cyan
Write-Host "  Run batch tests:   aestra test ./solution.exe --cases ./tests/" -ForegroundColor Cyan
Write-Host ""
