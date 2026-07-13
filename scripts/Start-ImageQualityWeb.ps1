param(
    [string]$HostName = "127.0.0.1",
    [int]$Port = 7860,
    [switch]$StatusOnly
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$ProjectRoot = Join-Path $RepoRoot "image-quality-report-vibecoding"
$TmpRoot = Join-Path $RepoRoot "tmp"
$OutLog = Join-Path $TmpRoot "image_quality_web_7860.out.log"
$ErrLog = Join-Path $TmpRoot "image_quality_web_7860.err.log"

function Get-ListeningPid {
    $systemRoot = $env:SystemRoot
    if (-not $systemRoot) {
        $systemRoot = "C:\Windows"
    }
    $netstat = Join-Path $systemRoot "System32\netstat.exe"
    $lines = & $netstat -ano 2>$null | Select-String -SimpleMatch ":$Port"
    foreach ($match in $lines) {
        $line = $match.Line
        $parts = ($line -split "\s+") | Where-Object { $_ }
        if ($parts.Count -ge 5 -and $parts[3] -eq "LISTENING") {
            return [int]$parts[4]
        }
    }
    return $null
}

function Resolve-Python {
    if ($env:IMAGE_QUALITY_PYTHON -and (Test-Path -LiteralPath $env:IMAGE_QUALITY_PYTHON)) {
        return $env:IMAGE_QUALITY_PYTHON
    }

    $candidates = @(
        (Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"),
        (Join-Path $ProjectRoot ".venv\Scripts\python.exe")
    )

    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) {
            return $candidate
        }
    }

    return "python"
}

New-Item -ItemType Directory -Force -Path $TmpRoot | Out-Null

$existingPid = Get-ListeningPid
if ($existingPid) {
    Write-Output "Image quality web UI is already running: http://$HostName`:$Port/ PID=$existingPid"
    exit 0
}

if ($StatusOnly) {
    Write-Output "Image quality web UI is not running on http://$HostName`:$Port/"
    exit 1
}

$python = Resolve-Python
$serverCommand = @"
`$env:PYTHONPATH = "src"
Set-Location -LiteralPath "$ProjectRoot"
& "$python" -m image_quality.web_app --host "$HostName" --port $Port 1>> "$OutLog" 2>> "$ErrLog"
"@
$encodedCommand = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($serverCommand))

$powershell = Join-Path $PSHOME "powershell.exe"
$startInfo = [System.Diagnostics.ProcessStartInfo]::new()
$startInfo.FileName = $powershell
$startInfo.Arguments = "-NoProfile -ExecutionPolicy Bypass -EncodedCommand $encodedCommand"
$startInfo.WorkingDirectory = $ProjectRoot
$startInfo.UseShellExecute = $false
$startInfo.CreateNoWindow = $true

# Some Codex/PowerShell environments expose both Path and PATH. ProcessStartInfo
# treats environment keys case-insensitively, so remove duplicate variants.
foreach ($key in @($startInfo.EnvironmentVariables.Keys)) {
    if ($key -cne "PATH" -and $key.ToUpperInvariant() -eq "PATH") {
        $startInfo.EnvironmentVariables.Remove($key)
    }
}

$process = [System.Diagnostics.Process]::Start($startInfo)

for ($attempt = 0; $attempt -lt 30; $attempt++) {
    Start-Sleep -Milliseconds 250
    $listeningPid = Get-ListeningPid
    if ($listeningPid) {
        Write-Output "Image quality web UI started: http://$HostName`:$Port/ PID=$listeningPid"
        exit 0
    }
}

Write-Error "Failed to start image quality web UI. Check logs: $OutLog and $ErrLog. Launcher PID=$($process.Id)"
