# Clean-LGPunch.ps1
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   LGPunch Registry Cleanup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 删除 App Paths
$appPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\App Paths\lgpunch.exe"
if (Test-Path $appPath) {
    Remove-Item -Path $appPath -Force
    Write-Host "[SUCCESS] App Paths entry removed." -ForegroundColor Green
} else {
    Write-Host "[INFO] App Paths entry not found." -ForegroundColor Yellow
}

# 2. 删除 Run 中的值
$runKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
try {
    $value = Get-ItemProperty -Path $runKey -Name "lgpunch" -ErrorAction Stop
    Remove-ItemProperty -Path $runKey -Name "lgpunch" -Force
    Write-Host "[SUCCESS] Startup entry removed." -ForegroundColor Green
} catch {
    Write-Host "[INFO] Startup entry not found." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   Cleanup complete!" -ForegroundColor Green
Write-Host "   You can now delete the lgpunch.exe folder manually if no longer needed."
Write-Host "========================================" -ForegroundColor Cyan
Read-Host "Press Enter to exit"