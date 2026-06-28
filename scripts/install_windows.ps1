param(
  [string]$InstallDir = "$env:USERPROFILE\ailovanta",
  [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

if (!(Test-Path $InstallDir)) {
  New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
}
Set-Location $InstallDir

if (!(Test-Path ".git")) {
  git clone https://github.com/ZqiEE/ailovanta.git .
} else {
  git pull --ff-only
}

python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\pip.exe install -r requirements.txt
New-Item -ItemType Directory -Force -Path runtime_data | Out-Null

@"
AILOVANTA_ENV=local
AILOVANTA_RATE_LIMIT_ENABLED=true
AILOVANTA_RATE_LIMIT_PER_MINUTE=120
AILOVANTA_RATE_LIMIT_WINDOW_SECONDS=60
AILOVANTA_REQUIRE_NODE_PROOF=true
AILOVANTA_MIN_AVG_TRUST_SCORE=0.75
"@ | Set-Content -Encoding UTF8 .env.local

@"
`$ErrorActionPreference = "Stop"
Set-Location "$InstallDir"
Get-Content .env.local | ForEach-Object {
  if (`$_ -match "^([^#][^=]+)=(.*)$") { [Environment]::SetEnvironmentVariable(`$matches[1], `$matches[2], "Process") }
}
.\.venv\Scripts\uvicorn.exe api.main_release_ready:app --host 0.0.0.0 --port $Port
"@ | Set-Content -Encoding UTF8 run.ps1

@"
`$ErrorActionPreference = "Stop"
Set-Location "$InstallDir"
.\.venv\Scripts\python.exe scripts\check_release.py --route-key owned-chat/default
"@ | Set-Content -Encoding UTF8 check.ps1

Write-Host "Installed to $InstallDir"
Write-Host "Run: powershell -ExecutionPolicy Bypass -File $InstallDir\run.ps1"
Write-Host "Check: powershell -ExecutionPolicy Bypass -File $InstallDir\check.ps1"
