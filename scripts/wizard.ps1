Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

[System.Windows.Forms.Application]::EnableVisualStyles()

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$icoPath = Join-Path $repoRoot "assets\aestra.ico"
$pngPath = Join-Path $repoRoot "assets\aestra.png"

$installDir = Join-Path $HOME ".aestra"
$binDir = Join-Path $installDir "bin"
$aestraBat = Join-Path $binDir "aestra.bat"

$script:isInstalled = (Test-Path $aestraBat)

$form = New-Object System.Windows.Forms.Form
$form.Text = "Aestra Setup Wizard (v1.0.1)"
$form.Size = New-Object System.Drawing.Size(580, 460)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::FixedDialog
$form.MaximizeBox = $false
$form.MinimizeBox = $true
$form.BackColor = [System.Drawing.Color]::FromArgb(15, 23, 42)
$form.ForeColor = [System.Drawing.Color]::FromArgb(241, 245, 249)
$form.TopMost = $true
$form.Add_Shown({
    $form.Activate()
    $form.TopMost = $false
})

if (Test-Path $icoPath) {
    try {
        $form.Icon = New-Object System.Drawing.Icon($icoPath)
    } catch {}
}

$headerPanel = New-Object System.Windows.Forms.Panel
$headerPanel.Size = New-Object System.Drawing.Size(580, 78)
$headerPanel.Location = New-Object System.Drawing.Point(0, 0)
$headerPanel.BackColor = [System.Drawing.Color]::FromArgb(11, 19, 43)

$logoBox = New-Object System.Windows.Forms.PictureBox
$logoBox.Size = New-Object System.Drawing.Size(50, 50)
$logoBox.Location = New-Object System.Drawing.Point(22, 14)
$logoBox.SizeMode = [System.Windows.Forms.PictureBoxSizeMode]::Zoom
$logoBox.BackColor = [System.Drawing.Color]::Transparent
if (Test-Path $pngPath) {
    try {
        $logoBox.Image = [System.Drawing.Image]::FromFile($pngPath)
    } catch {}
}
$headerPanel.Controls.Add($logoBox)

$titleLabel = New-Object System.Windows.Forms.Label
$titleLabel.Text = "Aestra Setup Wizard"
$titleLabel.Font = New-Object System.Drawing.Font("Segoe UI", 15, [System.Drawing.FontStyle]::Bold)
$titleLabel.ForeColor = [System.Drawing.Color]::FromArgb(56, 189, 248)
$titleLabel.Location = New-Object System.Drawing.Point(82, 14)
$titleLabel.AutoSize = $true

$subtitleLabel = New-Object System.Windows.Forms.Label
$subtitleLabel.Text = "Deterministic CP Execution Sandbox  *  v1.0.1 Stable"
$subtitleLabel.Font = New-Object System.Drawing.Font("Segoe UI", 9.5)
$subtitleLabel.ForeColor = [System.Drawing.Color]::FromArgb(148, 163, 184)
$subtitleLabel.Location = New-Object System.Drawing.Point(84, 44)
$subtitleLabel.AutoSize = $true

$headerPanel.Controls.Add($titleLabel)
$headerPanel.Controls.Add($subtitleLabel)
$form.Controls.Add($headerPanel)

$cardPanel = New-Object System.Windows.Forms.Panel
$cardPanel.Size = New-Object System.Drawing.Size(526, 175)
$cardPanel.Location = New-Object System.Drawing.Point(24, 94)
$cardPanel.BackColor = [System.Drawing.Color]::FromArgb(30, 41, 59)

$infoLabel = New-Object System.Windows.Forms.Label
$infoLabel.Font = New-Object System.Drawing.Font("Segoe UI", 9.5)
$infoLabel.ForeColor = [System.Drawing.Color]::FromArgb(226, 232, 240)
$infoLabel.Location = New-Object System.Drawing.Point(18, 14)
$infoLabel.Size = New-Object System.Drawing.Size(490, 105)

if ($script:isInstalled) {
    $infoLabel.Text = "Aestra v1.0.1 is currently installed on this system:`n`n" +
                      "  [OK]  Global 'aestra' command is available in your PATH`n" +
                      "  [OK]  Desktop shortcut configured at $HOME\Desktop\Aestra.lnk`n" +
                      "  [OK]  Core sandbox components located at $installDir`n" +
                      "  [OK]  Zero C++/Rust compiler requirements (Pure Python 3.10+)"
} else {
    $infoLabel.Text = "Configure Aestra on your system with one click:`n`n" +
                      "  *  Add 'aestra' command permanently to your user PATH`n" +
                      "  *  Create an 'Aestra' Desktop shortcut with branded App Icon`n" +
                      "  *  Zero C++/Rust compiler requirements (Python 3.10+ fallback engine)`n" +
                      "  *  Isolated sandbox with microsecond CPU and RAM telemetry"
}
$cardPanel.Controls.Add($infoLabel)

$envLabel = New-Object System.Windows.Forms.Label
$envLabel.Font = New-Object System.Drawing.Font("Segoe UI", 9)
$envLabel.Location = New-Object System.Drawing.Point(18, 130)
$envLabel.Size = New-Object System.Drawing.Size(490, 30)

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) { $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $pythonCmd) { $pythonCmd = Get-Command py -ErrorAction SilentlyContinue }

if ($pythonCmd) {
    $envLabel.Text = "[Detected] Python environment ready ($($pythonCmd.Source))"
    $envLabel.ForeColor = [System.Drawing.Color]::FromArgb(52, 211, 153)
} else {
    $envLabel.Text = "[Warning] Python 3.10+ not detected in PATH. Please install from python.org"
    $envLabel.ForeColor = [System.Drawing.Color]::FromArgb(248, 113, 113)
}
$cardPanel.Controls.Add($envLabel)
$form.Controls.Add($cardPanel)

$progressBar = New-Object System.Windows.Forms.ProgressBar
$progressBar.Location = New-Object System.Drawing.Point(24, 285)
$progressBar.Size = New-Object System.Drawing.Size(526, 16)
$progressBar.Minimum = 0
$progressBar.Maximum = 100
$progressBar.Value = if ($script:isInstalled) { 100 } else { 0 }
$form.Controls.Add($progressBar)

$statusLabel = New-Object System.Windows.Forms.Label
if ($script:isInstalled) {
    $statusLabel.Text = "Aestra is installed and ready to launch."
    $statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(52, 211, 153)
} else {
    $statusLabel.Text = "Ready to install. Click 'Install Aestra' to continue."
    $statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(148, 163, 184)
}
$statusLabel.Font = New-Object System.Drawing.Font("Segoe UI", 9)
$statusLabel.Location = New-Object System.Drawing.Point(24, 310)
$statusLabel.Size = New-Object System.Drawing.Size(526, 22)
$form.Controls.Add($statusLabel)

$buttonPanel = New-Object System.Windows.Forms.Panel
$buttonPanel.Size = New-Object System.Drawing.Size(580, 68)
$buttonPanel.Location = New-Object System.Drawing.Point(0, 348)
$buttonPanel.BackColor = [System.Drawing.Color]::FromArgb(11, 19, 43)

$installBtn = New-Object System.Windows.Forms.Button
$installBtn.Font = New-Object System.Drawing.Font("Segoe UI", 9.5, [System.Drawing.FontStyle]::Bold)
$installBtn.Size = New-Object System.Drawing.Size(145, 38)
$installBtn.Location = New-Object System.Drawing.Point(24, 15)
$installBtn.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
$installBtn.FlatAppearance.BorderSize = 0
$installBtn.Cursor = [System.Windows.Forms.Cursors]::Hand

if ($script:isInstalled) {
    $installBtn.Text = "Launch Aestra"
    $installBtn.BackColor = [System.Drawing.Color]::FromArgb(16, 185, 129)
    $installBtn.ForeColor = [System.Drawing.Color]::White
} else {
    $installBtn.Text = "Install Aestra"
    $installBtn.BackColor = [System.Drawing.Color]::FromArgb(14, 165, 233)
    $installBtn.ForeColor = [System.Drawing.Color]::White
}

$uninstallBtn = New-Object System.Windows.Forms.Button
$uninstallBtn.Text = "Uninstall"
$uninstallBtn.Font = New-Object System.Drawing.Font("Segoe UI", 9)
$uninstallBtn.Size = New-Object System.Drawing.Size(110, 38)
$uninstallBtn.Location = New-Object System.Drawing.Point(180, 15)
$uninstallBtn.BackColor = [System.Drawing.Color]::FromArgb(30, 41, 59)
$uninstallBtn.ForeColor = [System.Drawing.Color]::FromArgb(248, 113, 113)
$uninstallBtn.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
$uninstallBtn.FlatAppearance.BorderSize = 0
$uninstallBtn.Cursor = [System.Windows.Forms.Cursors]::Hand
$uninstallBtn.Visible = $script:isInstalled

$cancelBtn = New-Object System.Windows.Forms.Button
$cancelBtn.Text = if ($script:isInstalled) { "Close" } else { "Cancel" }
$cancelBtn.Font = New-Object System.Drawing.Font("Segoe UI", 9.5)
$cancelBtn.Size = New-Object System.Drawing.Size(110, 38)
$cancelBtn.Location = New-Object System.Drawing.Point(440, 15)
$cancelBtn.BackColor = [System.Drawing.Color]::FromArgb(30, 41, 59)
$cancelBtn.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225)
$cancelBtn.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
$cancelBtn.FlatAppearance.BorderSize = 0
$cancelBtn.Cursor = [System.Windows.Forms.Cursors]::Hand

$cancelBtn.Add_Click({
    $form.Close()
})

$uninstallBtn.Add_Click({
    $confirm = [System.Windows.Forms.MessageBox]::Show(
        "Are you sure you want to uninstall Aestra?`n`nThis will remove the 'aestra' command from PATH, delete Desktop shortcuts, and remove ~/.aestra.",
        "Confirm Uninstall",
        [System.Windows.Forms.MessageBoxButtons]::YesNo,
        [System.Windows.Forms.MessageBoxIcon]::Warning
    )
    if ($confirm -eq [System.Windows.Forms.DialogResult]::Yes) {
        $uninstallScript = Join-Path $repoRoot "scripts\uninstall.ps1"
        if (Test-Path $uninstallScript) {
            & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $uninstallScript -Quiet
        }
        $script:isInstalled = $false
        $statusLabel.Text = "Aestra has been completely uninstalled."
        $statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(248, 113, 113)
        $progressBar.Value = 0
        $installBtn.Text = "Install Aestra"
        $installBtn.BackColor = [System.Drawing.Color]::FromArgb(14, 165, 233)
        $uninstallBtn.Visible = $false
        $cancelBtn.Text = "Close"
    }
})

$installBtn.Add_Click({
    if ($script:isInstalled) {
        if (Test-Path $aestraBat) {
            Start-Process cmd.exe -ArgumentList "/k `"$aestraBat`""
        } else {
            Start-Process cmd.exe -ArgumentList "/k aestra"
        }
        $form.Close()
        return
    }

    $installBtn.Enabled = $false
    $cancelBtn.Enabled = $false
    $uninstallBtn.Enabled = $false

    $statusLabel.Text = "Checking Python environment..."
    $statusLabel.Refresh()
    $progressBar.Value = 20
    Start-Sleep -Milliseconds 250

    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) { $py = Get-Command python3 -ErrorAction SilentlyContinue }
    if (-not $py) { $py = Get-Command py -ErrorAction SilentlyContinue }

    if (-not $py) {
        $statusLabel.Text = "Error: Python 3.10+ not found! Please install from python.org"
        $statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(248, 113, 113)
        $installBtn.Enabled = $true
        $cancelBtn.Enabled = $true
        return
    }

    $statusLabel.Text = "Configuring .aestra directories..."
    $statusLabel.Refresh()
    $progressBar.Value = 40
    Start-Sleep -Milliseconds 200

    if (-not (Test-Path $binDir)) { New-Item -ItemType Directory -Force -Path $binDir | Out-Null }

    $srcSource = Join-Path $repoRoot "src"
    $srcDest = Join-Path $installDir "src"
    if (Test-Path $srcSource) {
        Copy-Item -Path $srcSource -Destination $srcDest -Recurse -Force -ErrorAction SilentlyContinue
    }

    Get-ChildItem -LiteralPath $installDir -Recurse -ErrorAction SilentlyContinue | Unblock-File -ErrorAction SilentlyContinue

    $statusLabel.Text = "Creating global CLI launcher shims..."
    $statusLabel.Refresh()
    $progressBar.Value = 60
    Start-Sleep -Milliseconds 200

    $batContent = "@echo off`r`nset PYTHONPATH=$installDir;%PYTHONPATH%`r`npython -m src.cli %*"
    Set-Content -Path (Join-Path $binDir "aestra.bat") -Value $batContent -Encoding Ascii
    Set-Content -Path (Join-Path $binDir "aestra.cmd") -Value $batContent -Encoding Ascii
    $localBatContent = "@echo off`r`nset PYTHONPATH=%~dp0;%PYTHONPATH%`r`npython -m src.cli %*"
    Set-Content -Path (Join-Path $repoRoot "aestra.bat") -Value $localBatContent -Encoding Ascii

    $pyScriptsDir = Join-Path (Split-Path $py.Source) "Scripts"
    if (Test-Path $pyScriptsDir) {
        Set-Content -Path (Join-Path $pyScriptsDir "aestra.bat") -Value $batContent -Encoding Ascii
        Set-Content -Path (Join-Path $pyScriptsDir "aestra.cmd") -Value $batContent -Encoding Ascii
    }

    $statusLabel.Text = "Configuring App Icon and Desktop shortcut..."
    $statusLabel.Refresh()
    $progressBar.Value = 80
    Start-Sleep -Milliseconds 200

    $assetsTarget = Join-Path $installDir "assets"
    if (-not (Test-Path $assetsTarget)) { New-Item -ItemType Directory -Force -Path $assetsTarget | Out-Null }
    $targetIco = Join-Path $assetsTarget "aestra.ico"
    if (Test-Path $icoPath) {
        Copy-Item $icoPath $targetIco -Force -ErrorAction SilentlyContinue
    }

    try {
        $wshShell = New-Object -ComObject WScript.Shell
        $desktopPath = [Environment]::GetFolderPath("Desktop")
        $shortcut = $wshShell.CreateShortcut((Join-Path $desktopPath "Aestra.lnk"))
        $shortcut.TargetPath = (Join-Path $binDir "aestra.bat")
        $shortcut.WorkingDirectory = $HOME
        $shortcut.Description = "Aestra - Deterministic CP Execution Sandbox"
        if (Test-Path $targetIco) { $shortcut.IconLocation = "$targetIco,0" }
        $shortcut.Save()
    } catch {}

    $statusLabel.Text = "Registering global PATH..."
    $statusLabel.Refresh()
    $progressBar.Value = 100

    $userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    if ($userPath -notlike "*$binDir*") {
        [Environment]::SetEnvironmentVariable("PATH", "$userPath;$binDir", "User")
    }

    $statusLabel.Text = "Installation complete! Aestra is ready to use."
    $statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(52, 211, 153)

    $script:isInstalled = $true
    $installBtn.Text = "Launch Aestra"
    $installBtn.BackColor = [System.Drawing.Color]::FromArgb(16, 185, 129)
    $installBtn.Enabled = $true
    $uninstallBtn.Visible = $true
    $uninstallBtn.Enabled = $true
    $cancelBtn.Text = "Close"
    $cancelBtn.Enabled = $true
})

$buttonPanel.Controls.Add($installBtn)
$buttonPanel.Controls.Add($uninstallBtn)
$buttonPanel.Controls.Add($cancelBtn)
$form.Controls.Add($buttonPanel)

[void]$form.ShowDialog()
