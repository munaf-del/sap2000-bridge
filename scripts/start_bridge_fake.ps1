$ErrorActionPreference = "Stop"

$env:SAP2000_BRIDGE_ADAPTER_MODE = "fake"
$env:SAP2000_BRIDGE_ENABLE_REAL_COM = "0"

Write-Host "Starting SAP2000 Local Bridge in fake mode."
Write-Host "Loopback only: http://127.0.0.1:8765"
Write-Host "Real COM disabled. No write-back."

python -m uvicorn bridge.api.main:app --host 127.0.0.1 --port 8765

