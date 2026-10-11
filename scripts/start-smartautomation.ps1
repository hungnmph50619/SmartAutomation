# One-click SmartAutomation startup. Safe to run more than once.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$frontend = Join-Path $root "frontend"
$ufoDefault = Join-Path $env:USERPROFILE "Downloads\SmartAutomation-feat-v0.1-ufo-foundation\SmartAutomation-feat-v0.1-ufo-foundation\vendor\UFO"
$ufoRoot = if ($env:SMARTAUTOMATION_UFO_ROOT) { $env:SMARTAUTOMATION_UFO_ROOT } else { $ufoDefault }
$ufoPythonDefault = Join-Path (Split-Path -Parent (Split-Path -Parent $ufoRoot)) ".venv\Scripts\python.exe"
$ufoPython = if ($env:SMARTAUTOMATION_UFO_PYTHON) { $env:SMARTAUTOMATION_UFO_PYTHON } else { $ufoPythonDefault }

if (-not (Test-Path (Join-Path $ufoRoot "ufo\__main__.py"))) {
  throw "UFO source not found at $ufoRoot. Set SMARTAUTOMATION_UFO_ROOT before launching."
}
if (-not (Test-Path $ufoPython)) {
  throw "UFO Python not found at $ufoPython. Set SMARTAUTOMATION_UFO_PYTHON before launching."
}
if (-not (Test-Path (Join-Path $frontend "node_modules\vite"))) {
  throw "Frontend dependencies missing. Run 'npm.cmd install' once in the frontend folder."
}
$null = Get-Command py -ErrorAction Stop
$null = Get-Command npm.cmd -ErrorAction Stop

function Test-ListeningPort([int]$Port) {
  $client = New-Object System.Net.Sockets.TcpClient
  try {
    $async = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
    if (-not $async.AsyncWaitHandle.WaitOne(400)) { return $false }
    try { $client.EndConnect($async); return $true } catch { return $false }
  } finally { $client.Close() }
}
function Test-BackendReady {
  try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8765/api/jobs/current" -UseBasicParsing -TimeoutSec 2
    return ($response.StatusCode -eq 200)
  } catch { return $false }
}
function Test-FrontendReady {
  try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:5173/" -UseBasicParsing -TimeoutSec 2
    return ($response.StatusCode -eq 200)
  } catch { return $false }
}

$env:SMARTAUTOMATION_UFO_ROOT = $ufoRoot
$env:SMARTAUTOMATION_UFO_PYTHON = $ufoPython
# This only enables the consent-gated backend API; users must still opt in per task.
$env:SMARTAUTOMATION_EXECUTION_ENABLED = "true"

Write-Host "Starting SmartAutomation..." -ForegroundColor Cyan
if (-not (Test-BackendReady)) {
  if (Test-ListeningPort 8765) {
    throw "Port 8765 belongs to another service or an unhealthy backend. Close it before starting."
  }
  Start-Process -FilePath "cmd.exe" -WorkingDirectory $root -ArgumentList @("/k", "title SmartAutomation Backend && py -3.11 -m uvicorn smartautomation.api:app --host 127.0.0.1 --port 8765") | Out-Null
  Write-Host "Backend window launched."
} else { Write-Host "Backend already running." }

if (-not (Test-FrontendReady)) {
  if (Test-ListeningPort 5173) {
    throw "Port 5173 belongs to another service or an unhealthy frontend. Close it before starting."
  }
  Start-Process -FilePath "cmd.exe" -WorkingDirectory $frontend -ArgumentList @("/k", "title SmartAutomation Frontend && npm.cmd run dev -- --strictPort") | Out-Null
  Write-Host "Frontend window launched."
} else { Write-Host "Frontend already running." }

$ready = $false
for ($i = 0; $i -lt 30; $i++) {
  if ((Test-BackendReady) -and (Test-FrontendReady)) { $ready = $true; break }
  Start-Sleep -Seconds 1
}
if (-not $ready) { throw "Startup timed out. Read Backend and Frontend windows for errors." }
Start-Process "http://127.0.0.1:5173/"
Write-Host "SmartAutomation ready at http://127.0.0.1:5173/" -ForegroundColor Green
