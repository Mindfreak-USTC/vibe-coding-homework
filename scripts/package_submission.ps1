param(
    [string]$Python = "",
    [switch]$SkipVerification,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Root = $Root.Path
$DistDir = Join-Path $Root "dist"
$SourceZip = Join-Path $DistDir "vibe-coding-homework-source.zip"
$HistoryBundle = Join-Path $DistDir "vibe-coding-homework-history.bundle"
$ShaFile = Join-Path $DistDir "SHA256SUMS.txt"

function Invoke-CommandOrDryRun {
    param(
        [string]$Exe,
        [string[]]$ArgumentList
    )

    if ($DryRun) {
        Write-Host ("DRY RUN: " + $Exe + " " + ($ArgumentList -join " "))
        return
    }

    & $Exe @ArgumentList
    if ($LASTEXITCODE -ne 0) {
        throw "$Exe $($ArgumentList -join ' ') failed with exit code $LASTEXITCODE"
    }
}

function Assert-CleanWorktree {
    $dirty = git -C $Root status --short
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to read git status"
    }

    if (-not [string]::IsNullOrWhiteSpace(($dirty -join "`n"))) {
        throw "Working tree has uncommitted changes. Commit or revert them before packaging."
    }
}

Write-Host "Submission package helper"
Write-Host "Root: $Root"
Write-Host "Dist: $DistDir"

if ($DryRun) {
    Write-Host "DRY RUN enabled. No package files will be changed."
} else {
    Assert-CleanWorktree
    New-Item -ItemType Directory -Force $DistDir | Out-Null
}

Invoke-CommandOrDryRun `
    -Exe "git" `
    -ArgumentList @("-C", $Root, "archive", "--format=zip", "--output=$SourceZip", "HEAD")

Invoke-CommandOrDryRun `
    -Exe "git" `
    -ArgumentList @("-C", $Root, "bundle", "create", $HistoryBundle, "--all")

if ($DryRun) {
    Write-Host "DRY RUN: update $ShaFile with current HEAD and package hashes"
} else {
    $head = git -C $Root rev-parse HEAD
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to resolve current HEAD"
    }
    $zipHash = Get-FileHash -Algorithm SHA256 $SourceZip
    $bundleHash = Get-FileHash -Algorithm SHA256 $HistoryBundle
    $lines = @(
        "HEAD  $head",
        "",
        "SHA256  $($zipHash.Hash)  vibe-coding-homework-source.zip",
        "SHA256  $($bundleHash.Hash)  vibe-coding-homework-history.bundle"
    )
    Set-Content -Encoding UTF8 -Path $ShaFile -Value $lines
    Get-Content -Encoding UTF8 $ShaFile
}

if (-not $SkipVerification) {
    $verifyArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "scripts\verify_submission.ps1")
    if (-not [string]::IsNullOrWhiteSpace($Python)) {
        $verifyArgs += @("-Python", $Python)
    }

    if ($DryRun) {
        Write-Host ("DRY RUN: powershell " + ($verifyArgs -join " "))
    } else {
        & powershell @verifyArgs
        if ($LASTEXITCODE -ne 0) {
            throw "Submission verification failed with exit code $LASTEXITCODE"
        }
    }
}
