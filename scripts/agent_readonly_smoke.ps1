$ErrorActionPreference = "Stop"

$BaseUrl = "http://127.0.0.1:8765"
$ModelPath = "C:\SAP2000BridgeWorkspace\smoke_frame_2point.sdb"
$Errors = @()

function Invoke-BridgeGet {
    param([string]$Path)
    Invoke-RestMethod -Method Get -Uri "$BaseUrl$Path"
}

function Invoke-BridgePost {
    param(
        [string]$Path,
        [object]$Body
    )
    Invoke-RestMethod -Method Post -Uri "$BaseUrl$Path" -ContentType "application/json" -Body ($Body | ConvertTo-Json -Depth 8)
}

Write-Host "Running approved read-only SAP2000 bridge smoke on $BaseUrl"
Write-Host "No analysis, no result extraction, no patch/apply, no write-back."

try { $health = Invoke-BridgeGet "/health" } catch { $Errors += "health: $($_.Exception.Message)" }
try { $info = Invoke-BridgeGet "/bridge/info" } catch { $Errors += "bridge-info: $($_.Exception.Message)" }
try { $statusBefore = Invoke-BridgeGet "/sap2000/status" } catch { $Errors += "status-before: $($_.Exception.Message)" }
try { $connect = Invoke-BridgePost "/sap2000/connect" @{ attach_to_running = $true } } catch { $Errors += "connect: $($_.Exception.Message)" }
try { $openModel = Invoke-BridgePost "/sap2000/open-model" @{ path = $ModelPath; copy_to_workspace = $false } } catch { $Errors += "open-model: $($_.Exception.Message)" }
try { $units = Invoke-BridgeGet "/sap2000/model/units" } catch { $Errors += "units: $($_.Exception.Message)" }
try { $joints = Invoke-BridgeGet "/sap2000/model/joints" } catch { $Errors += "joints: $($_.Exception.Message)" }
try { $frames = Invoke-BridgeGet "/sap2000/model/frames" } catch { $Errors += "frames: $($_.Exception.Message)" }
try { $materials = Invoke-BridgeGet "/sap2000/model/materials" } catch { $Errors += "materials: $($_.Exception.Message)" }
try { $sections = Invoke-BridgeGet "/sap2000/model/sections" } catch { $Errors += "sections: $($_.Exception.Message)" }
try { $patterns = Invoke-BridgeGet "/sap2000/model/load-patterns" } catch { $Errors += "load-patterns: $($_.Exception.Message)" }
try { $cases = Invoke-BridgeGet "/sap2000/model/load-cases" } catch { $Errors += "load-cases: $($_.Exception.Message)" }
try { $combinations = Invoke-BridgeGet "/sap2000/model/load-combinations" } catch { $Errors += "load-combinations: $($_.Exception.Message)" }
try { $audit = Invoke-BridgeGet "/sap2000/audit" } catch { $Errors += "audit: $($_.Exception.Message)" }

$summary = [ordered]@{
    adapter_mode = $info.adapter_mode
    sap2000_version = $connect.version_label
    model_path = $openModel.model_path
    units = $units.units.present
    joint_count = @($joints.joints).Count
    frame_count = @($frames.frames).Count
    material_count = @($materials.materials).Count
    section_count = @($sections.sections).Count
    load_pattern_count = @($patterns.load_patterns).Count
    load_case_count = @($cases.load_cases).Count
    load_combination_count = @($combinations.load_combinations).Count
    audit_count = @($audit.records).Count
    errors = $Errors
}

$summary | ConvertTo-Json -Depth 8

if ($Errors.Count -gt 0) {
    exit 1
}

