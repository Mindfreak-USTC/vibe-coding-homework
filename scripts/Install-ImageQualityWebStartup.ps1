param(
    [int]$Port = 7860
)

$ErrorActionPreference = "Stop"

$WatchScript = Join-Path $PSScriptRoot "Watch-ImageQualityWeb.ps1"
if (-not (Test-Path -LiteralPath $WatchScript)) {
    throw "Watch script not found: $WatchScript"
}

$StartupDir = [Environment]::GetFolderPath("Startup")
if (-not $StartupDir) {
    throw "Cannot resolve current user's Startup folder."
}

$StartupFile = Join-Path $StartupDir "ImageQualityWebWatch.cmd"
$command = "@echo off`r`n" +
    "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$WatchScript`" -Port $Port`r`n"
Set-Content -LiteralPath $StartupFile -Encoding ASCII -Value $command

$powershell = Join-Path $PSHOME "powershell.exe"
$arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$WatchScript`" -Port $Port"
$startInfo = [System.Diagnostics.ProcessStartInfo]::new()
$startInfo.FileName = $powershell
$startInfo.Arguments = $arguments
$startInfo.WorkingDirectory = Split-Path -Parent $PSScriptRoot
$startInfo.UseShellExecute = $false
$startInfo.CreateNoWindow = $true

foreach ($key in @($startInfo.EnvironmentVariables.Keys)) {
    if ($key -cne "PATH" -and $key.ToUpperInvariant() -eq "PATH") {
        $startInfo.EnvironmentVariables.Remove($key)
    }
}

$process = [System.Diagnostics.Process]::Start($startInfo)
Start-Sleep -Seconds 2
& (Join-Path $PSScriptRoot "Start-ImageQualityWeb.ps1") -Port $Port
Write-Output "Startup watchdog installed: $StartupFile"
Write-Output "Watchdog PID=$($process.Id)"
