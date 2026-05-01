$ErrorActionPreference = "Stop"

$env:SAP2000_BRIDGE_ADAPTER_MODE = "comtypes"
$env:SAP2000_BRIDGE_ENABLE_REAL_COM = "1"
$env:SAP2000_EXE_PATH = "C:\Program Files\Computers and Structures\SAP2000 27\SAP2000.exe"
$env:SAP2000_WORKSPACE = "C:\SAP2000BridgeWorkspace"

Write-Host "Starting SAP2000 Local Bridge in guarded real COM mode."
Write-Host "Native Windows PowerShell only. Do not use Docker, WSL, or Ubuntu."
Write-Host "Loopback only: http://127.0.0.1:8765"
Write-Host "Do not bind this bridge to all network interfaces."
Write-Host "No write-back. No create, modify, delete, assign, save, or overwrite operations."

python -m uvicorn bridge.api.main:app --host 127.0.0.1 --port 8765

