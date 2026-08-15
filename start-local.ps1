$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$Python = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    $Python = "py"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $Python = "python"
} else {
    Write-Error "Python 3.11+ is required. Install Python, then rerun .\start-local.ps1"
}

if (-not (Test-Path ".venv")) {
    if ($Python -eq "py") { & py -3 -m venv .venv } else { & python -m venv .venv }
}

& .\.venv\Scripts\python.exe -m pip install --disable-pip-version-check -q -r requirements-coding.txt
& .\.venv\Scripts\python.exe -m node_client.local_runtime @args
