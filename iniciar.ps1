$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$candidates = @(
    (Join-Path $PSScriptRoot '.venv\Scripts\python.exe'),
    (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe')
)
foreach ($name in @('python', 'py')) {
    $command = Get-Command $name -ErrorAction SilentlyContinue
    if ($command) { $candidates += $command.Source }
}
foreach ($candidate in $candidates) {
    if (-not (Test-Path -LiteralPath $candidate)) { continue }
    try {
        & $candidate -c 'from PySide6 import QtWidgets; import PIL' 2>$null
        if ($LASTEXITCODE -eq 0) {
            & $candidate (Join-Path $PSScriptRoot 'app.py')
            exit $LASTEXITCODE
        }
    } catch { continue }
}
Write-Host 'Dependencias do Pixel Livre nao encontradas.'
Write-Host 'Na pasta do projeto, execute:'
Write-Host 'python -m venv .venv'
Write-Host '.\.venv\Scripts\python.exe -m pip install -r requirements.txt'
Read-Host 'Pressione Enter para fechar'
