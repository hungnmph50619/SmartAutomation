param(
    [string]$TaskName = "notepad-acceptance",
    [int]$TimeoutSeconds = 600
)
$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $root

if (-not $IsWindows -and $PSVersionTable.PSEdition -eq "Core") {
    throw "This test requires interactive Windows."
}
$ufo = Join-Path $root "vendor\UFO"
if (-not (Test-Path (Join-Path $ufo "ufo\ufo.py"))) {
    throw "Microsoft UFO source missing: run .\scripts\bootstrap-ufo.ps1"
}
if ($env:SMARTAUTOMATION_EXECUTION_ENABLED -ne "true") {
    throw 'Set $env:SMARTAUTOMATION_EXECUTION_ENABLED="true" after reviewing what UFO will do.'
}
Write-Host "Close confidential documents and use a non-production Windows desktop."
Write-Host "The UFO agent may interact with windows on your desktop."
$prompt = 'Open Windows Notepad. Type exactly: SmartAutomation UFO Windows acceptance test. Do not save or modify other files.'
python -m smartautomation.ufo --task $TaskName --request $prompt --execute --timeout $TimeoutSeconds
$exitCode = $LASTEXITCODE
Write-Host "UFO process exit code: $exitCode"
Write-Host "MANUAL ACCEPTANCE: Look at Notepad and verify the exact text."
Write-Host "A zero exit code does not prove the task succeeded."
if ($exitCode -ne 0) { throw "UFO ended with exit code $exitCode" }
