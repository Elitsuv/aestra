Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

[System.Windows.Forms.Application]::EnableVisualStyles()

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$icoPath = Join-Path $repoRoot "assets\aestra.ico"

$form = New-Object System.Windows.Forms.Form
$form.Text = "Aestra Setup Wizard (v1.0.0)"
$form.Size = New-Object System.Drawing.Size(540, 420)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::FixedDialog
$form.MaximizeBox = $false
$form.MinimizeBox = $true
$form.BackColor = [System.Drawing.Color]::FromArgb(245, 247, 250)

if (Test-Path $icoPath) {
    try {
        $form.Icon = New-Object System.Drawing.Icon($icoPath)
    } catch {}
}

# Header Banner
$headerPanel = New-Object System.Windows.Forms.Panel
$headerPanel.Size = New-Object System.Drawing.Size(540, 80)
$headerPanel.Location = New-Object System.Drawing.Point(0, 0)
$headerPanel.BackColor = [System.Drawing.Color]::FromArgb(15, 23, 42) # Slate 900

$titleLabel = New-Object System.Windows.Forms.Label
$titleLabel.Text = "Aestra Setup Wizard"
$titleLabel.Font = New-Object System.Drawing.Font("Segoe UI", 16, [System.Drawing.FontStyle]::Bold)
$titleLabel.ForeColor = [System.Drawing.Color]::FromArgb(56, 189, 248) # Cyan 400
$titleLabel.Location = New-Object System.Drawing.Point(24, 14)
$titleLabel.AutoSize = $true

$subtitleLabel = New-Object System.Windows.Forms.Label
$subtitleLabel.Text = "Deterministic Competitive Programming Sandbox * v1.0.0 Stable"
$subtitleLabel.Font = New-Object System.Drawing.Font("Segoe UI", 9.5)
$subtitleLabel.ForeColor = [System.Drawing.Color]::FromArgb(203, 213, 225) # Slate 300
$subtitleLabel.Location = New-Object System.Drawing.Point(26, 46)
$subtitleLabel.AutoSize = $true

$headerPanel.Controls.Add($titleLabel)
$headerPanel.Controls.Add($subtitleLabel)
$form.Controls.Add($headerPanel)

# Body Section
$infoLabel = New-Object System.Windows.Forms.Label
$infoLabel.Text = "Welcome to Aestra setup. This wizard will configure Aestra on your system:`n`n" +
                  "  *  Add 'aestra' command permanently to your user PATH`n" +
                  "  *  Create an 'Aestra' Desktop shortcut with the branded App Icon`n" +
                  "  *  Detect Python 3.10+ and available compilers (g++, rustc, go)`n" +
                  "  *  Zero admin rights required, zero host directory pollution"
$infoLabel.Font = New-Object System.Drawing.Font("Segoe UI", 9.5)
$infoLabel.ForeColor = [System.Drawing.Color]::FromArgb(51, 65, 85)
$infoLabel.Location = New-Object System.Drawing.Point(26, 100)
$infoLabel.Size = New-Object System.Drawing.Size(480, 130)
$form.Controls.Add($infoLabel)

# Progress Bar
$progressBar = New-Object System.Windows.Forms.ProgressBar
$progressBar.Location = New-Object System.Drawing.Point(26, 240)
$progressBar.Size = New-Object System.Drawing.Size(472, 22)
$progressBar.Minimum = 0
$progressBar.Maximum = 100
$progressBar.Value = 0
$form.Controls.Add($progressBar)

# Status Label
$statusLabel = New-Object System.Windows.Forms.Label
$statusLabel.Text = "Ready to install. Click 'Install Aestra' to continue."
$statusLabel.Font = New-Object System.Drawing.Font("Segoe UI", 9)
$statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(100, 116, 139)
$statusLabel.Location = New-Object System.Drawing.Point(26, 270)
$statusLabel.Size = New-Object System.Drawing.Size(472, 22)
$form.Controls.Add($statusLabel)

# Footer Buttons
$buttonPanel = New-Object System.Windows.Forms.Panel
$buttonPanel.Size = New-Object System.Drawing.Size(540, 60)
$buttonPanel.Location = New-Object System.Drawing.Point(0, 320)
$buttonPanel.BackColor = [System.Drawing.Color]::FromArgb(238, 242, 246)

$installBtn = New-Object System.Windows.Forms.Button
$installBtn.Text = "Install Aestra"
$installBtn.Font = New-Object System.Drawing.Font("Segoe UI", 10, [System.Drawing.FontStyle]::Bold)
$installBtn.Size = New-Object System.Drawing.Size(140, 36)
$installBtn.Location = New-Object System.Drawing.Point(230, 12)
$installBtn.BackColor = [System.Drawing.Color]::FromArgb(14, 165, 233)
$installBtn.ForeColor = [System.Drawing.Color]::White
$installBtn.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
$installBtn.Cursor = [System.Windows.Forms.Cursors]::Hand

$cancelBtn = New-Object System.Windows.Forms.Button
$cancelBtn.Text = "Cancel"
$cancelBtn.Font = New-Object System.Drawing.Font("Segoe UI", 9.5)
$cancelBtn.Size = New-Object System.Drawing.Size(100, 36)
$cancelBtn.Location = New-Object System.Drawing.Point(385, 12)
$cancelBtn.BackColor = [System.Drawing.Color]::White
$cancelBtn.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
$cancelBtn.Cursor = [System.Windows.Forms.Cursors]::Hand

$cancelBtn.Add_Click({
    $form.Close()
})

$isInstalled = $false

$installBtn.Add_Click({
    if ($isInstalled) {
        # Launch Aestra interactive shell in a new terminal window
        $installDir = Join-Path $HOME ".aestra"
        $binDir = Join-Path $installDir "bin"
        $aestraBat = Join-Path $binDir "aestra.bat"
        if (Test-Path $aestraBat) {
            Start-Process cmd.exe -ArgumentList "/k `"$aestraBat`""
        }
        $form.Close()
        return
    }

    $installBtn.Enabled = $false
    $cancelBtn.Enabled = $false

    # Step 1: Check Python
    $statusLabel.Text = "Checking Python environment..."
    $statusLabel.Refresh()
    $progressBar.Value = 20
    Start-Sleep -Milliseconds 300

    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCmd) { $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue }
    if (-not $pythonCmd) { $pythonCmd = Get-Command py -ErrorAction SilentlyContinue }

    if (-not $pythonCmd) {
        $statusLabel.Text = "Error: Python 3.10+ not found! Please install from python.org"
        $statusLabel.ForeColor = [System.Drawing.Color]::Red
        $installBtn.Enabled = $true
        return
    }

    # Step 2: Set up directory
    $statusLabel.Text = "Configuring .aestra directories..."
    $statusLabel.Refresh()
    $progressBar.Value = 40
    Start-Sleep -Milliseconds 300

    $installDir = Join-Path $HOME ".aestra"
    $binDir = Join-Path $installDir "bin"
    if (-not (Test-Path $binDir)) { New-Item -ItemType Directory -Force -Path $binDir | Out-Null }

    # Copy core src files to ensure application works even if download folder is moved or deleted
    $srcSource = Join-Path $repoRoot "src"
    $srcDest = Join-Path $installDir "src"
    if (Test-Path $srcSource) {
        Copy-Item -Path $srcSource -Destination $srcDest -Recurse -Force -ErrorAction SilentlyContinue
    }

    # Step 3: Write shims
    $statusLabel.Text = "Creating global CLI launcher shims..."
    $statusLabel.Refresh()
    $progressBar.Value = 60

    $batContent = "@echo off`r`nset PYTHONPATH=$installDir;%PYTHONPATH%`r`npython -m src.cli %*"
    Set-Content -Path (Join-Path $binDir "aestra.bat") -Value $batContent -Encoding Ascii
    Set-Content -Path (Join-Path $binDir "aestra.cmd") -Value $batContent -Encoding Ascii

    # Step 4: Desktop shortcut and Icon
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

    # Step 5: PATH variable
    $statusLabel.Text = "Registering global PATH..."
    $statusLabel.Refresh()
    $progressBar.Value = 100

    $userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    if ($userPath -notlike "*$binDir*") {
        [Environment]::SetEnvironmentVariable("PATH", "$userPath;$binDir", "User")
    }

    # Success State
    $statusLabel.Text = "Installation complete! Aestra is ready to use."
    $statusLabel.ForeColor = [System.Drawing.Color]::FromArgb(22, 163, 74) # Green 600

    $isInstalled = $true
    $installBtn.Text = "Launch Aestra"
    $installBtn.BackColor = [System.Drawing.Color]::FromArgb(22, 163, 74)
    $installBtn.Enabled = $true
    $cancelBtn.Text = "Close"
    $cancelBtn.Enabled = $true
})

$buttonPanel.Controls.Add($installBtn)
$buttonPanel.Controls.Add($cancelBtn)
$form.Controls.Add($buttonPanel)

[void]$form.ShowDialog()
