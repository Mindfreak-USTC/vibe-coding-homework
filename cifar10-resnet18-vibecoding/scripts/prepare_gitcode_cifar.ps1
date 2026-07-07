param(
    [string]$RepoUrl = "https://gitcode.com/open-source-toolkit/94ecd.git",
    [string]$DataDir = "data",
    [string]$WorkDir = "../tmp/gitcode-cifar",
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

$dataPath = Resolve-Path -LiteralPath $DataDir -ErrorAction SilentlyContinue
if (-not $dataPath) {
    New-Item -ItemType Directory -Force -Path $DataDir | Out-Null
    $dataPath = Resolve-Path -LiteralPath $DataDir
}

if (Test-Path -LiteralPath $WorkDir) {
    Remove-Item -LiteralPath $WorkDir -Recurse -Force
}

git clone --depth 1 $RepoUrl $WorkDir
$archive = Join-Path $WorkDir "cifar-10-python.tar.gz"
if (-not (Test-Path -LiteralPath $archive)) {
    throw "Archive not found after clone: $archive"
}

# The GitCode file is named .tar.gz but its README says it is RAR content.
# Windows tar.exe can list and extract it directly.
tar -xf $archive -C $dataPath

& $Python -c "from torchvision.datasets import CIFAR10; ds=CIFAR10(root='$DataDir', train=True, download=False); print('CIFAR-10 train images:', len(ds))"
if ($LASTEXITCODE -ne 0) {
    throw "CIFAR-10 extraction finished, but Python verification failed. Activate the project environment or pass -Python <path-to-python>."
}
