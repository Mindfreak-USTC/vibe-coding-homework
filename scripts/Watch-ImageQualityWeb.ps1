param(
    [int]$Port = 7860,
    [int]$IntervalSeconds = 30
)

$ErrorActionPreference = "Continue"

$StartScript = Join-Path $PSScriptRoot "Start-ImageQualityWeb.ps1"
$TmpRoot = Join-Path (Split-Path -Parent $PSScriptRoot) "tmp"
$WatchLog = Join-Path $TmpRoot "image_quality_web_watchdog.log"
New-Item -ItemType Directory -Force -Path $TmpRoot | Out-Null

while ($true) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    try {
        $message = & $StartScript -Port $Port 2>&1
        Add-Content -LiteralPath $WatchLog -Encoding UTF8 -Value "[$timestamp] $message"
    }
    catch {
        Add-Content -LiteralPath $WatchLog -Encoding UTF8 -Value "[$timestamp] ERROR: $($_.Exception.Message)"
    }
    Start-Sleep -Seconds $IntervalSeconds
}
