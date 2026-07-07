param(
    [string]$Python = "",
    [switch]$SkipTests,
    [switch]$RequireRemote
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Root = $Root.Path

if ([string]::IsNullOrWhiteSpace($Python)) {
    $BundledPython = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
    if (Test-Path $BundledPython) {
        $Python = $BundledPython
    } else {
        $Python = "python"
    }
}

function Invoke-Native {
    param(
        [string]$Name,
        [string]$WorkingDirectory,
        [string]$Exe,
        [string[]]$ArgumentList,
        [hashtable]$Env = @{}
    )

    Write-Host ""
    Write-Host "== $Name"

    $oldEnv = @{}
    foreach ($key in $Env.Keys) {
        $oldEnv[$key] = [Environment]::GetEnvironmentVariable($key, "Process")
        [Environment]::SetEnvironmentVariable($key, [string]$Env[$key], "Process")
    }

    Push-Location $WorkingDirectory
    try {
        & $Exe @ArgumentList
        if ($LASTEXITCODE -ne 0) {
            throw "$Name failed with exit code $LASTEXITCODE"
        }
    } finally {
        Pop-Location
        foreach ($key in $Env.Keys) {
            [Environment]::SetEnvironmentVariable($key, $oldEnv[$key], "Process")
        }
    }
}

function Assert-FileExists {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        throw "Missing required file: $Path"
    }
}

Write-Host "Submission verification"
Write-Host "Root: $Root"
Write-Host "Python: $Python"

$requiredFiles = @(
    "TEACHER_HANDOFF.md",
    "ACCEPTANCE_AUDIT.md",
    "PROJECT_MANAGEMENT_REPORT.md",
    "SUBMISSION_CHECKLIST.md",
    "scripts\verify_submission.ps1",
    "cifar10-resnet18-vibecoding\outputs\report.md",
    "cifar10-resnet18-vibecoding\outputs\test_metrics.json",
    "cifar10-resnet18-vibecoding\outputs\confusion_matrix.png",
    "cifar10-resnet18-vibecoding\outputs\training_curves.png",
    "image-quality-report-vibecoding\outputs\quality_results.csv",
    "image-quality-report-vibecoding\outputs\report.md",
    "image-quality-report-vibecoding\outputs\issue_counts.png",
    "dist\vibe-coding-homework-source.zip",
    "dist\vibe-coding-homework-history.bundle",
    "dist\SHA256SUMS.txt"
)

foreach ($relativePath in $requiredFiles) {
    Assert-FileExists (Join-Path $Root $relativePath)
}

if (-not $SkipTests) {
    Invoke-Native `
        -Name "CIFAR unittest" `
        -WorkingDirectory (Join-Path $Root "cifar10-resnet18-vibecoding") `
        -Exe $Python `
        -ArgumentList @("-m", "unittest", "discover", "-s", "tests", "-v")

    Invoke-Native `
        -Name "CIFAR compileall" `
        -WorkingDirectory (Join-Path $Root "cifar10-resnet18-vibecoding") `
        -Exe $Python `
        -ArgumentList @("-m", "compileall", "src", "tests")

    Invoke-Native `
        -Name "Image quality unittest" `
        -WorkingDirectory (Join-Path $Root "image-quality-report-vibecoding") `
        -Exe $Python `
        -ArgumentList @("-m", "unittest", "discover", "-s", "tests", "-v") `
        -Env @{ "PYTHONPATH" = "src" }

    Invoke-Native `
        -Name "Image quality compileall" `
        -WorkingDirectory (Join-Path $Root "image-quality-report-vibecoding") `
        -Exe $Python `
        -ArgumentList @("-m", "compileall", "src", "tests")
}

Invoke-Native `
    -Name "Git bundle verify" `
    -WorkingDirectory $Root `
    -Exe "git" `
    -ArgumentList @("bundle", "verify", "dist\vibe-coding-homework-history.bundle")

Write-Host ""
Write-Host "== Source zip content check"
$zipEntries = & tar -tf (Join-Path $Root "dist\vibe-coding-homework-source.zip")
if ($LASTEXITCODE -ne 0) {
    throw "Unable to list source zip"
}

$requiredZipEntries = @(
    "TEACHER_HANDOFF.md",
    "ACCEPTANCE_AUDIT.md",
    "PROJECT_MANAGEMENT_REPORT.md",
    "SUBMISSION_CHECKLIST.md",
    "scripts/verify_submission.ps1",
    "cifar10-resnet18-vibecoding/outputs/training_curves.png",
    "image-quality-report-vibecoding/outputs/quality_results.csv"
)

foreach ($entry in $requiredZipEntries) {
    if ($zipEntries -notcontains $entry) {
        throw "Source zip is missing required entry: $entry"
    }
}

$badPattern = '(^|/)\.git/|checkpoints/.*\.pth|data/cifar|logs/events|tmp/'
$badEntries = $zipEntries | Select-String -Pattern $badPattern
if ($badEntries) {
    $badEntries | ForEach-Object { Write-Host $_.Line }
    throw "Source zip contains excluded entries"
}
Write-Host "Source zip includes required entries and excludes generated heavy files."

Write-Host ""
Write-Host "== SHA256SUMS check"
$currentHead = git -C $Root rev-parse HEAD
if ($LASTEXITCODE -ne 0) {
    throw "git rev-parse failed"
}
$shaLines = Get-Content -Encoding UTF8 (Join-Path $Root "dist\SHA256SUMS.txt")
$expectedHeadLine = "HEAD  $currentHead"
if ($shaLines -notcontains $expectedHeadLine) {
    throw "SHA256SUMS.txt does not reference current HEAD $currentHead"
}
$zipHash = (Get-FileHash -Algorithm SHA256 (Join-Path $Root "dist\vibe-coding-homework-source.zip")).Hash
$bundleHash = (Get-FileHash -Algorithm SHA256 (Join-Path $Root "dist\vibe-coding-homework-history.bundle")).Hash
if ($shaLines -notcontains "SHA256  $zipHash  vibe-coding-homework-source.zip") {
    throw "SHA256SUMS.txt source zip hash is stale"
}
if ($shaLines -notcontains "SHA256  $bundleHash  vibe-coding-homework-history.bundle") {
    throw "SHA256SUMS.txt bundle hash is stale"
}
Write-Host "SHA256SUMS.txt matches current HEAD and dist files."

Write-Host ""
Write-Host "== Git status"
Push-Location $Root
try {
    git status --short --branch
    if ($LASTEXITCODE -ne 0) {
        throw "git status failed"
    }
    $dirty = git status --short
    if ($LASTEXITCODE -ne 0) {
        throw "git status --short failed"
    }
    if (-not [string]::IsNullOrWhiteSpace(($dirty -join "`n"))) {
        throw "Working tree has uncommitted changes. Commit or revert them before submitting."
    }

    $commitCount = git rev-list --count HEAD
    if ($LASTEXITCODE -ne 0) {
        throw "git rev-list failed"
    }
    Write-Host "Commit count: $commitCount"

    $remote = git remote -v
    if ($LASTEXITCODE -ne 0) {
        throw "git remote failed"
    }
    if ([string]::IsNullOrWhiteSpace($remote)) {
        Write-Warning "No Git remote is configured. Local submission package is ready, but remote push is not complete."
        if ($RequireRemote) {
            throw "Remote is required but not configured."
        }
    } else {
        Write-Host $remote
    }
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "Local submission verification passed."
