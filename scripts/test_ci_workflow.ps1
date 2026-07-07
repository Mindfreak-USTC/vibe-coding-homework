$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Root = $Root.Path
$WorkflowPath = Join-Path $Root ".github\workflows\ci.yml"

if (-not (Test-Path $WorkflowPath)) {
    throw "Missing GitHub Actions workflow: $WorkflowPath"
}

$workflow = Get-Content -Raw -Encoding UTF8 $WorkflowPath

$requiredSnippets = @(
    "actions/checkout@v4",
    "actions/setup-python@v5",
    "cifar10-resnet18-vibecoding/requirements.txt",
    "image-quality-report-vibecoding/requirements.txt",
    "cifar10-resnet18-vibecoding",
    "image-quality-report-vibecoding",
    "python -m unittest discover -s tests -v",
    "python -m compileall src tests",
    "scripts/test_push_remote.ps1"
)

foreach ($snippet in $requiredSnippets) {
    if ($workflow -notmatch [regex]::Escape($snippet)) {
        throw "Workflow is missing required snippet: $snippet"
    }
}

if ($workflow -match "verify_submission\.ps1") {
    throw "Workflow should not call verify_submission.ps1 because dist/ is not tracked in fresh checkout"
}

Write-Host "ci.yml structure test passed"
