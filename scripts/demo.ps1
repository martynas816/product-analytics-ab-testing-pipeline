# Run the demo pipeline (Windows / PowerShell)
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\scripts\demo.ps1

$ErrorActionPreference = "Stop"

Write-Host "==> Stopping any previous containers (and removing volumes)..." -ForegroundColor Cyan
try {
  docker compose down -v | Out-Host
} catch {
  # ignore
}

Write-Host "==> Building + running the demo (aborts if pipeline fails)..." -ForegroundColor Cyan
Write-Host "If it fails, run this to debug dbt:" -ForegroundColor DarkGray
Write-Host "  docker compose up -d postgres" -ForegroundColor DarkGray
Write-Host "  docker compose run --rm --entrypoint sh pipeline" -ForegroundColor DarkGray
Write-Host "  # then inside: dbt build --project-dir /app/dbt --profiles-dir /app/dbt --debug" -ForegroundColor DarkGray


docker compose up --build --abort-on-container-exit
