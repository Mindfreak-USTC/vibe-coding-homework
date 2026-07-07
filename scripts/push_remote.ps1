param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$RemoteUrl,
    [string]$RemoteName = "origin",
    [string]$Branch = "master",
    [string]$Python = "",
    [switch]$ReplaceRemote,
    [switch]$SkipVerification,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Root = $Root.Path

function Invoke-Git {
    param(
        [string[]]$ArgumentList
    )

    if ($DryRun) {
        Write-Host ("DRY RUN: git " + ($ArgumentList -join " "))
        return
    }

    & git @ArgumentList
    if ($LASTEXITCODE -ne 0) {
        throw "git $($ArgumentList -join ' ') failed with exit code $LASTEXITCODE"
    }
}

function Get-ExistingRemoteUrl {
    param([string]$Name)

    $remoteNames = git -C $Root remote
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to list git remotes"
    }

    if ($remoteNames -contains $Name) {
        $url = git -C $Root remote get-url $Name
        if ($LASTEXITCODE -ne 0) {
            throw "Unable to read git remote URL for $Name"
        }
        return ($url -join "").Trim()
    }

    return ""
}

function Assert-CleanWorktree {
    $dirty = git -C $Root status --short
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to read git status"
    }

    if (-not [string]::IsNullOrWhiteSpace(($dirty -join "`n"))) {
        throw "Working tree has uncommitted changes. Commit or revert them before pushing."
    }
}

Push-Location $Root
try {
    Write-Host "Remote push helper"
    Write-Host "Root: $Root"
    Write-Host "Remote: $RemoteName -> $RemoteUrl"
    Write-Host "Branch: $Branch"

    if ($DryRun) {
        Write-Host "DRY RUN enabled. No remote will be changed and no push will run."
    } else {
        Assert-CleanWorktree
    }

    $currentBranch = git branch --show-current
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to read current branch"
    }
    $currentBranch = ($currentBranch -join "").Trim()
    if ($currentBranch -ne $Branch) {
        Write-Warning "Current branch is '$currentBranch', but script will push branch '$Branch'."
    }

    $existingRemoteUrl = Get-ExistingRemoteUrl -Name $RemoteName
    if ([string]::IsNullOrWhiteSpace($existingRemoteUrl)) {
        Invoke-Git -ArgumentList @("remote", "add", $RemoteName, $RemoteUrl)
    } elseif ($existingRemoteUrl -eq $RemoteUrl) {
        Write-Host "Remote $RemoteName already points to $RemoteUrl"
    } elseif ($ReplaceRemote) {
        Invoke-Git -ArgumentList @("remote", "set-url", $RemoteName, $RemoteUrl)
    } elseif ($DryRun) {
        Write-Host "DRY RUN: remote $RemoteName currently points to $existingRemoteUrl; real run would require -ReplaceRemote to change it."
    } else {
        throw "Remote $RemoteName already points to $existingRemoteUrl. Use -ReplaceRemote to update it."
    }

    Invoke-Git -ArgumentList @("push", "-u", $RemoteName, $Branch)

    if (-not $SkipVerification) {
        $verifyArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "scripts\verify_submission.ps1", "-RequireRemote")
        if (-not [string]::IsNullOrWhiteSpace($Python)) {
            $verifyArgs += @("-Python", $Python)
        }

        if ($DryRun) {
            Write-Host ("DRY RUN: powershell " + ($verifyArgs -join " "))
        } else {
            & powershell @verifyArgs
            if ($LASTEXITCODE -ne 0) {
                throw "Post-push submission verification failed with exit code $LASTEXITCODE"
            }
        }
    }
} finally {
    Pop-Location
}
