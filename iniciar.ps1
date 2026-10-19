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
        & $candidate -c 'import tkinter; import PIL' 2>$null
        if ($LASTEXITCODE -eq 0) {
            & $candidate (Join-Path $PSScriptRoot 'app.py')
            exit $LASTEXITCODE
        }
    } catch { continue }
}
Write-Host 'Python com Tkinter e Pillow nao encontrado.'
Write-Host 'Instale Python e execute: python -m pip install -r requirements.txt'
Read-Host 'Pressione Enter para fechar'
