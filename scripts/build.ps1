# Build-LGPunch.ps1
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

# Step 1: Build
Write-Host "[Step 1] Building with Nuitka ..." -ForegroundColor Yellow
& nuitka --onefile --standalone --windows-console-mode=attach src/main.py --output-filename="lgpunch.exe" --output-dir="dist"
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

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Build and packaging completed!" -ForegroundColor Green
Write-Host "   Output is in: release\"
Write-Host "========================================" -ForegroundColor Cyan
Read-Host "Press Enter to exit"