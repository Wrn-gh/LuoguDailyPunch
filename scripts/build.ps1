# Build-LGPunch.ps1
param(
    [string]$upx = ""
)

# PowerShell 不会把 --upx 当作命名参数，这里统一归一化
$tokens = @()
if ($upx) { $tokens += $upx }
$tokens += @($args)

$value = ""
$consumed = 0
if ($tokens.Count -ge 1) {
    $first = [string]$tokens[0]
    if ($first -eq '--upx' -or $first -eq '-upx') {
        if ($tokens.Count -ge 2) {
            $value = [string]$tokens[1]
            $consumed = 2
        } else {
            Write-Host "[ERROR] --upx requires a path, e.g. --upx `"D:\path\to\upx.exe`"" -ForegroundColor Red
            exit 1
        }
    } elseif ($first.StartsWith('--upx=')) {
        $value = $first.Substring(6)
        $consumed = 1
    } elseif ($first.StartsWith('-upx=')) {
        $value = $first.Substring(5)
        $consumed = 1
    } elseif ($first.StartsWith('-')) {
        Write-Host "[ERROR] Unknown argument: $first" -ForegroundColor Red
        Write-Host "Usage: .\build.ps1 [--upx `"<upx.exe>`"]" -ForegroundColor Yellow
        exit 1
    } else {
        $value = $first
        $consumed = 1
    }
}
if ($tokens.Count -gt $consumed) {
    Write-Host "[ERROR] Unexpected argument: $($tokens[$consumed])" -ForegroundColor Red
    Write-Host "Usage: .\build.ps1 [--upx `"<upx.exe>`"]" -ForegroundColor Yellow
    exit 1
}
$upx = $value

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   LGPunch Build and Package Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path "src\main.py")) {
    Write-Host "[ERROR] src/main.py not found!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not (Get-Command nuitka -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Nuitka is not installed." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Resolve UPX (opt-in: only used when --upx is given)
$upxArgs = @()
if ($upx) {
    if (-not (Test-Path -LiteralPath $upx)) {
        Write-Host "[ERROR] UPX not found: $upx" -ForegroundColor Red
        exit 1
    }
    $upxArgs = @("--enable-plugins=upx", "--upx-binary=$upx", "--onefile-no-compression")
    Write-Host "[INFO] UPX: $upx" -ForegroundColor Green
} else {
    Write-Host "[INFO] UPX disabled (use --upx `"<path>`" to enable)" -ForegroundColor DarkGray
}

# Step 1: Build
Write-Host "[Step 1] Building with Nuitka ..." -ForegroundColor Yellow
& nuitka --onefile --standalone --windows-console-mode=attach `
src/main.py `
--disable-plugins=pywebview `
--lto=yes `
@upxArgs `
--output-filename="lgpunch.exe" `
--output-dir="dist"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Build failed!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "[SUCCESS] Build completed." -ForegroundColor Green

# Step 2: Create release in root
Write-Host ""
Write-Host "[Step 2] Creating release package in root ..." -ForegroundColor Yellow
if (-not (Test-Path "release")) {
    New-Item -Path "release" -ItemType Directory | Out-Null
}

Copy-Item -Path "dist\lgpunch.exe" -Destination "release\lgpunch.exe" -Force
if ($?) {
    Write-Host "[SUCCESS] lgpunch.exe copied to release." -ForegroundColor Green
} else {
    Write-Host "[WARNING] Copy failed." -ForegroundColor Yellow
}

if (Test-Path "scripts/setup.ps1") {
    Copy-Item -Path "scripts/setup.ps1" -Destination "release\setup.ps1" -Force
    if ($?) {
        Write-Host "[SUCCESS] setup.ps1 copied to release." -ForegroundColor Green
    } else {
        Write-Host "[WARNING] Copy failed." -ForegroundColor Yellow
    }
} else {
    Write-Host "[WARNING] setup.ps1 not found, skipping." -ForegroundColor Yellow
}

if (Test-Path "release\ui") {
    Remove-Item "release\ui" -Recurse -Force
}
if (Test-Path "ui") {
    Copy-Item -Path "ui" -Destination "release\ui" -Recurse -Force
    if ($?) {
        Write-Host "[SUCCESS] ui copied to release\ui." -ForegroundColor Green
    } else {
        Write-Host "[WARNING] ui copy failed." -ForegroundColor Yellow
    }
} else {
    Write-Host "[WARNING] ui not found, skipping." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Build and packaging completed!" -ForegroundColor Green
Write-Host "   Output is in: release\"
Write-Host "========================================" -ForegroundColor Cyan
Read-Host "Press Enter to exit"