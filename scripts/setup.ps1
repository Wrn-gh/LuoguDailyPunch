<#
.SYNOPSIS
    Luogu Daily Punch (lgpunch) Setup Script

.DESCRIPTION
    Registers lgpunch.exe, optionally sets UID/Client ID, adds to PATH, and adds auto-start.

.PARAMETER ExePath
    Optional. Specifies the full or relative path to lgpunch.exe.
    If omitted, the script will auto-detect.

.PARAMETER Help
    Shows this help message.
#>

param(
    [string]$ExePath,
    [switch]$Help
)

if ($Help) {
    Get-Help $MyInvocation.MyCommand.Path -Detailed
    exit 0
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Luogu Daily Punch (lgpunch) Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ---------- Locate lgpunch.exe ----------
$exeFile = $null
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if ($scriptDir -is [array]) { $scriptDir = $scriptDir[0] }
$scriptDir = $scriptDir.TrimEnd('\')

if ($ExePath) {
    if (-not [System.IO.Path]::IsPathRooted($ExePath)) {
        $ExePath = Join-Path (Get-Location).Path $ExePath
    }
    if (Test-Path $ExePath) {
        $exeFile = $ExePath
        Write-Host "[INFO] Using user-specified: $exeFile" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Specified file does not exist: $ExePath" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    $candidates = @(
        "$scriptDir\lgpunch.exe",
        "$scriptDir\..\dist\lgpunch.exe",
        "$scriptDir\..\release\lgpunch.exe",
        "$scriptDir\dist\lgpunch.exe",
        "$scriptDir\release\lgpunch.exe"
    )

    Write-Host "[INFO] Script directory: $scriptDir" -ForegroundColor Gray
    Write-Host "[INFO] Searching in:" -ForegroundColor Yellow
    foreach ($cand in $candidates) {
        Write-Host "  - $cand" -ForegroundColor Gray
        if (Test-Path $cand) {
            $exeFile = (Get-Item $cand).FullName
            Write-Host "[FOUND] $exeFile" -ForegroundColor Green
            break
        }
    }
}

if (-not $exeFile) {
    Write-Host ""
    Write-Host "[ERROR] Cannot locate lgpunch.exe!" -ForegroundColor Red
    Write-Host "Please ensure one of the following exists:" -ForegroundColor Yellow
    Write-Host "  - $scriptDir\lgpunch.exe"
    Write-Host "  - $scriptDir\..\dist\lgpunch.exe"
    Write-Host "  - $scriptDir\..\release\lgpunch.exe"
    Write-Host "  - $scriptDir\dist\lgpunch.exe"
    Write-Host "  - $scriptDir\release\lgpunch.exe"
    Write-Host ""
    Write-Host "Alternatively, specify with -ExePath:"
    Write-Host "  .\setup.ps1 -ExePath `"D:\path\to\lgpunch.exe`""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[INFO] Found program: $exeFile" -ForegroundColor Green
$exeDir = Split-Path -Parent $exeFile
Write-Host "[INFO] Executable directory: $exeDir" -ForegroundColor Gray
Write-Host ""

# ---------- 1. Register to App Paths (optional) ----------
$doAppPath = Read-Host "Register to 'App Paths' so you can run via Win+R? (y/n)"
if ($doAppPath -match "^(y|yes)$") {
    Write-Host "[Step 1] Registering to App Paths ..." -ForegroundColor Yellow
    try {
        New-Item -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\App Paths\lgpunch.exe" -Force | Out-Null
        Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\App Paths\lgpunch.exe" -Name "(Default)" -Value $exeFile
        Write-Host "[SUCCESS] Registered." -ForegroundColor Green
    } catch {
        Write-Host "[WARNING] Registration failed (optional)." -ForegroundColor Yellow
    }
} else {
    Write-Host "[INFO] Skipping App Paths registration." -ForegroundColor Yellow
}
Write-Host ""

# ---------- 2. Configure credentials (optional) ----------
$doCred = Read-Host "Configure UID and Client ID? (y/n)"
if ($doCred -match "^(y|yes)$") {
    Write-Host ""
    Write-Host "[Step 2] Please provide your Luogu credentials:"
    do {
        $uid = Read-Host "Enter UID: "
    } while ([string]::IsNullOrWhiteSpace($uid))

    do {
        $cid = Read-Host "Enter Client ID: "
    } while ([string]::IsNullOrWhiteSpace($cid))

    Write-Host ""
    Write-Host "[Step 3] Saving credentials ..." -ForegroundColor Yellow
    $setArgs = @("set", "--uid", $uid, "--cid", $cid)
    $process = Start-Process -FilePath $exeFile -ArgumentList $setArgs -Wait -NoNewWindow -PassThru
    if ($process.ExitCode -ne 0) {
        Write-Host "[ERROR] Setting failed." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    } else {
        Write-Host "[SUCCESS] Saved." -ForegroundColor Green
    }
} else {
    Write-Host "[INFO] Skipping credential configuration." -ForegroundColor Yellow
}
Write-Host ""

# ---------- 3. Add to PATH (optional) ----------
$doPath = Read-Host "Add lgpunch.exe directory to user PATH environment variable? (y/n)"
if ($doPath -match "^(y|yes)$") {
    Write-Host "[Step 4] Adding to user PATH ..." -ForegroundColor Yellow
    # 获取当前用户 PATH
    $path = [Environment]::GetEnvironmentVariable("Path", "User")
    $newPath = "$exeDir"
    # 检查是否已存在
    $existing = $path -split ';' | Where-Object { $_ -eq $newPath }
    if ($existing) {
        Write-Host "[INFO] Path already exists in user PATH." -ForegroundColor Gray
    } else {
        $newPathValue = $path + ";" + $newPath
        [Environment]::SetEnvironmentVariable("Path", $newPathValue, "User")
        Write-Host "[SUCCESS] Added to user PATH." -ForegroundColor Green
        Write-Host "[INFO] You may need to restart your terminal for the change to take effect." -ForegroundColor Gray
    }
} else {
    Write-Host "[INFO] Skipping PATH addition." -ForegroundColor Yellow
}
Write-Host ""

# ---------- 4. Add to startup (optional) ----------
$doStartup = Read-Host "Add to Windows startup (auto-punch on login)? (y/n)"
if ($doStartup -match "^(y|yes)$") {
    Write-Host "[Step 5] Adding to Windows startup ..." -ForegroundColor Yellow
    $startupPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
    try {
        Set-ItemProperty -Path $startupPath -Name "lgpunch" -Value "`"$exeFile`" punch"
        Write-Host "[SUCCESS] Startup entry added." -ForegroundColor Green
    } catch {
        Write-Host "[WARNING] Startup entry could not be added." -ForegroundColor Yellow
    }
} else {
    Write-Host "[INFO] Skipping startup entry." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setup complete!" -ForegroundColor Green
if ($doStartup -match "^(y|yes)$") {
    Write-Host "  Auto-punch will run at next login."
}
if ($doPath -match "^(y|yes)$") {
    Write-Host "  PATH updated - you can now type 'lgpunch' from any terminal."
}
Write-Host "  Manual run: `"$exeFile`" punch"
if ($doCred -notmatch "^(y|yes)$") {
    Write-Host "  Note: Credentials not configured. Use `"$exeFile`" set --uid ... --cid ..."
}
Write-Host "========================================" -ForegroundColor Cyan
Read-Host "Press Enter to exit"