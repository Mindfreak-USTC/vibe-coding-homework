$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Root = $Root.Path
$ScriptPath = Join-Path $PSScriptRoot "package_submission.ps1"
$ShaPath = Join-Path $Root "dist\SHA256SUMS.txt"

if (-not (Test-Path $ScriptPath)) {
    throw "Missing package helper script: $ScriptPath"
}

if (-not (Test-Path $ShaPath)) {
    throw "Missing SHA256SUMS.txt before dry-run"
}

$shaBefore = Get-Content -Raw -Encoding UTF8 $ShaPath

$output = & powershell -NoProfile -ExecutionPolicy Bypass -File $ScriptPath -DryRun -SkipVerification 2>&1
$exitCode = $LASTEXITCODE
$outputText = $output -join "`n"

if ($exitCode -ne 0) {
    Write-Host $outputText
    throw "package_submission.ps1 dry-run failed with exit code $exitCode"
}

if ($outputText -notmatch "DRY RUN") {
    Write-Host $outputText
    throw "Dry-run output did not include DRY RUN marker"
}

$shaAfter = Get-Content -Raw -Encoding UTF8 $ShaPath
if ($shaBefore -ne $shaAfter) {
    throw "Dry-run modified SHA256SUMS.txt"
}

Write-Host "package_submission.ps1 dry-run test passed"
