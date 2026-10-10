$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$frontend = Join-Path $root "frontend"
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "Node.js/npm is not installed. Install Node.js LTS, then reopen PowerShell."
}
Set-Location $frontend
if (-not (Test-Path (Join-Path $frontend "node_modules"))) {
    & npm install --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) { throw "npm install failed" }
}
& npm run dev
if ($LASTEXITCODE -ne 0) { throw "Frontend failed to start" }
