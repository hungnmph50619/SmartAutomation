param(
    [string]$UpstreamUrl = "https://github.com/microsoft/UFO.git",
    [string]$Revision = ""
)
$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$vendor = Join-Path $projectRoot "vendor"
$ufo = Join-Path $vendor "UFO"
New-Item -ItemType Directory -Path $vendor -Force | Out-Null

if (-not (Test-Path $ufo)) {
    & git clone $UpstreamUrl $ufo
    if ($LASTEXITCODE -ne 0) { throw "Cannot clone Microsoft UFO" }
}
if ($Revision) {
    & git -C $ufo fetch origin $Revision
    if ($LASTEXITCODE -ne 0) { throw "Cannot fetch UFO revision" }
    & git -C $ufo checkout --detach $Revision
    if ($LASTEXITCODE -ne 0) { throw "Cannot check out UFO revision" }
}
$sha = (& git -C $ufo rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0) { throw "Cannot resolve UFO revision" }
Write-Host "Microsoft UFO checkout: $ufo"
Write-Host "Pinned for this local run: $sha"
Write-Host "Next: follow UFO's official installation and provider setup instructions."
Write-Host "Keep agents.yaml and secrets outside SmartAutomation Git history."
