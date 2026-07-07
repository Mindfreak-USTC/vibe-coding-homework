$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Root = $Root.Path
$ScriptPath = Join-Path $PSScriptRoot "push_remote.ps1"

if (-not (Test-Path $ScriptPath)) {
    throw "Missing push helper script: $ScriptPath"
}

$remoteBefore = (git -C $Root remote -v) -join "`n"
if ($LASTEXITCODE -ne 0) {
    throw "Unable to read remotes before dry-run"
}

$output = & powershell -NoProfile -ExecutionPolicy Bypass -File $ScriptPath `
    -RemoteUrl "https://example.com/example/vibe-coding-homework.git" `
    -DryRun 2>&1
$exitCode = $LASTEXITCODE
$outputText = $output -join "`n"

if ($exitCode -ne 0) {
    Write-Host $outputText
    throw "push_remote.ps1 dry-run failed with exit code $exitCode"
}

if ($outputText -notmatch "DRY RUN") {
    Write-Host $outputText
    throw "Dry-run output did not include DRY RUN marker"
}

$remoteAfter = (git -C $Root remote -v) -join "`n"
if ($LASTEXITCODE -ne 0) {
    throw "Unable to read remotes after dry-run"
}

if ($remoteBefore -ne $remoteAfter) {
    throw "Dry-run modified git remotes"
}

Write-Host "push_remote.ps1 dry-run test passed"
