param()

$ErrorActionPreference = "Stop"

$repoDir = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$runtimeRoot = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies"
$presentationsRoot = Join-Path $env:USERPROFILE ".codex\plugins\cache\openai-primary-runtime\presentations"
$skillDir = Get-ChildItem -LiteralPath $presentationsRoot -Directory |
    Sort-Object Name -Descending |
    ForEach-Object { Join-Path $_.FullName "skills\presentations" } |
    Where-Object { Test-Path -LiteralPath $_ } |
    Select-Object -First 1

if (-not $skillDir) {
    throw "A skill de apresentações do Codex não foi encontrada."
}

$runtimeNode = Join-Path $runtimeRoot "node\bin\node.exe"
$runtimePython = Join-Path $runtimeRoot "python\python.exe"
$runtimeNodeModules = Join-Path $runtimeRoot "node\node_modules"
$nodeModulesLink = Join-Path $PSScriptRoot "node_modules"

foreach ($requiredPath in @($runtimeNode, $runtimePython, $runtimeNodeModules)) {
    if (-not (Test-Path -LiteralPath $requiredPath)) {
        throw "Dependência de geração não encontrada: $requiredPath"
    }
}

if (-not (Test-Path -LiteralPath $nodeModulesLink)) {
    New-Item -ItemType Junction -Path $nodeModulesLink -Target $runtimeNodeModules | Out-Null
}

$env:REPO_DIR = $repoDir
$env:SKILL_DIR = $skillDir
$env:RUNTIME_NODE = $runtimeNode
$env:RUNTIME_NODE_MODULES = $runtimeNodeModules
$env:RUNTIME_PYTHON = $runtimePython

& $runtimeNode (Join-Path $PSScriptRoot "build_decks.mjs")
$nodeExitCode = $LASTEXITCODE

$expectedOutputs = @(
    (Join-Path $repoDir "docs\apresentacao\pitch\MelodIA_Pitch.pptx"),
    (Join-Path $repoDir "docs\apresentacao\pitch\MelodIA_Pitch.pdf"),
    (Join-Path $repoDir "docs\apresentacao\tecnica\MelodIA_Tecnica.pptx"),
    (Join-Path $repoDir "docs\apresentacao\tecnica\MelodIA_Tecnica.pdf")
)
$receipts = @(
    (Join-Path $repoDir ".presentation-build\MelodIA_Pitch\MelodIA_Pitch.pptx.validation.json"),
    (Join-Path $repoDir ".presentation-build\MelodIA_Tecnica\MelodIA_Tecnica.pptx.validation.json")
)

$missing = $expectedOutputs | Where-Object { -not (Test-Path -LiteralPath $_) }
$invalidReceipts = $receipts | Where-Object {
    if (-not (Test-Path -LiteralPath $_)) { return $true }
    $receipt = Get-Content -LiteralPath $_ -Raw | ConvertFrom-Json
    return ($receipt.packageIntegrity.status -ne "pass" -or
        -not $receipt.presentationLayout.font_policy.passed -or
        -not $receipt.firstPartyImport.passed)
}

if ($missing.Count -gt 0 -or $invalidReceipts.Count -gt 0) {
    throw "A geração ou a validação não terminou corretamente (código $nodeExitCode)."
}

Write-Host "Decks, prévias e PDFs gerados e validados."
