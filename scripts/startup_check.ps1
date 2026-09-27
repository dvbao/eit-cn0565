<#
Systematic post-restart check for the CN0565 + ADICUP3029 stack.

Runs, in order: list COM ports -> IIO context check -> one sanity impedance
reading (routed through the UART timing proxy by default, since a direct
serial WRITE can silently drop its payload on this firmware). Stops at the
first failure and prints the troubleshooting command to run next, instead of
guessing further.

Usage:
    .\scripts\startup_check.ps1                  # lists ports, then tells you to pass -Port
    .\scripts\startup_check.ps1 -Port COM7
    .\scripts\startup_check.ps1 -Port COM7 -NoProxy
    .\scripts\startup_check.ps1 -Port COM7 -Pair 0,3,1,2
#>

[CmdletBinding()]
param(
    [string]$Port,
    [int]$Baud = 230400,
    [int[]]$Pair = @(0, 1, 2, 3),
    [switch]$NoProxy
)

$ErrorActionPreference = 'Stop'
$workspace = Split-Path $PSScriptRoot -Parent
$python = Join-Path $workspace 'cn0565-env\Scripts\python.exe'

if (-not (Test-Path $python)) {
    Write-Host "FAILED: $python not found. Run .\bootstrap-cn0565-env.ps1 first." -ForegroundColor Red
    exit 1
}

function Step($title) {
    Write-Host ""
    Write-Host "== $title ==" -ForegroundColor Cyan
}

Step "1/3 Danh sach cong COM"
& $python (Join-Path $workspace 'scripts\list_serial_ports.py')

if (-not $Port) {
    Write-Host ""
    Write-Host "Chon cong COM cua thiet bi (VID:PID=0D28:0204) roi chay lai voi -Port, vi du:" -ForegroundColor Yellow
    Write-Host "  .\scripts\startup_check.ps1 -Port COM7"
    exit 1
}

Step "2/3 Kiem tra IIO context tren $Port @ $Baud"
& $python (Join-Path $workspace 'scripts\check_connection.py') --port $Port --baud $Baud
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "FAILED tai buoc kiem tra IIO (exit $LASTEXITCODE)." -ForegroundColor Red
    Write-Host "Khong nap lai firmware ngay. Truoc tien xac nhan firmware co boot khong" -ForegroundColor Yellow
    Write-Host "(nhan nut S1/3029_RESET vat ly khi script yeu cau):"
    Write-Host "  $python scripts\capture_boot.py --port $Port --baud 115200"
    Write-Host "Neu khong thay banner 'Running IIOD server...', xem docs\connection-checklist.md muc 'Khi bi timeout'."
    exit $LASTEXITCODE
}

Step "3/3 Do thu 1 cap dien cuc (sanity check)"
$proxyArgs = @()
if (-not $NoProxy) {
    $proxyArgs = @('--proxy')
    Write-Host "(dung UART timing proxy de tranh loi drop WRITE payload cua firmware ADuCM3029)"
}
$pairArgs = $Pair | ForEach-Object { [string]$_ }
& $python (Join-Path $workspace 'scripts\run_official_example.py') single --port $Port --pair @pairArgs @proxyArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "FAILED tai buoc do thu (exit $LASTEXITCODE)." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "=== THIET BI SAN SANG DO EIT (COM=$Port, baud=$Baud) ===" -ForegroundColor Green
