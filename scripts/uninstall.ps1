[CmdletBinding()]
param(
    [switch]$Quiet,
    [switch]$Gui
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

function Invoke-Uninstall {
    $removedItems = @()

    $desktopPath = [Environment]::GetFolderPath("Desktop")
    $shortcutPath = Join-Path $desktopPath "Aestra.lnk"
    if (Test-Path $shortcutPath) {
        Remove-Item -Path $shortcutPath -Force -ErrorAction SilentlyContinue
        $removedItems += "Desktop shortcut"
    }

    $installDir = Join-Path $HOME ".aestra"
    $binDir = Join-Path $installDir "bin"
    $userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    if ($userPath -like "*$binDir*") {
        $pathEntries = $userPath -split ';' | Where-Object { $_ -and ($_ -ne $binDir) -and ($_ -ne "$binDir\") }
        $newPath = $pathEntries -join ';'
        [Environment]::SetEnvironmentVariable("PATH", $newPath, "User")
        $removedItems += "User PATH entry"
    }

    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCmd) { $pythonCmd = Get-Command py -ErrorAction SilentlyContinue }
    if ($pythonCmd) {
        $pyScriptsDir = Join-Path (Split-Path $pythonCmd.Source) "Scripts"
        $pyBat = Join-Path $pyScriptsDir "aestra.bat"
        $pyCmd = Join-Path $pyScriptsDir "aestra.cmd"
        if (Test-Path $pyBat) { Remove-Item $pyBat -Force -ErrorAction SilentlyContinue }
        if (Test-Path $pyCmd) { Remove-Item $pyCmd -Force -ErrorAction SilentlyContinue }
    }

    if (Test-Path $installDir) {
        Remove-Item -Path $installDir -Recurse -Force -ErrorAction SilentlyContinue
        $removedItems += ".aestra core directory ($installDir)"
    }

    return $removedItems
}

if ($Gui -or (-not $Quiet -and [Environment]::UserInteractive -and -not $Host.Name.Contains("Server"))) {
    $confirm = [System.Windows.Forms.MessageBox]::Show(
        "Are you sure you want to completely uninstall Aestra?`n`nThis will remove the Aestra command, desktop shortcut, and all configuration files in ~/.aestra.",
        "Uninstall Aestra v1.0.1",
        [System.Windows.Forms.MessageBoxButtons]::YesNo,
        [System.Windows.Forms.MessageBoxIcon]::Question
    )

    if ($confirm -eq [System.Windows.Forms.DialogResult]::Yes) {
        $items = Invoke-Uninstall
        [System.Windows.Forms.MessageBox]::Show(
            "Aestra has been completely removed from your system.`n`nRemoved:`n  - " + ($items -join "`n  - "),
            "Aestra Uninstalled",
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Information
        )
    }
} else {
    Write-Host "`n  [*] Uninstalling Aestra..." -ForegroundColor Cyan
    $items = Invoke-Uninstall
    Write-Host "  [OK] Successfully removed Aestra from your system." -ForegroundColor Green
    foreach ($item in $items) {
        Write-Host "       - $item" -ForegroundColor Gray
    }
    Write-Host ""
}
