$ErrorActionPreference = "Stop"

$connections = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue

if (-not $connections) {
    Write-Host "No SAP2000 Local Bridge listener found on 127.0.0.1:8765."
    exit 0
}

$processIds = $connections | Select-Object -ExpandProperty OwningProcess -Unique

foreach ($processId in $processIds) {
    $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
    if ($null -eq $process) {
        continue
    }

    Write-Host "Stopping process $processId listening on 127.0.0.1:8765 ($($process.ProcessName))."
    Stop-Process -Id $processId -Force
}

