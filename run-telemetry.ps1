<#
Kill/remove existing container (if present), pull latest image, then run the Aspire Dashboard.

Exposes:
- OTLP gRPC   : localhost:4317   (Python backend)
- OTLP HTTP   : localhost:4318   (Browser frontend)
- Dashboard UI: http://localhost:18888
#>

$ErrorActionPreference = "Stop"

$containerName = "otel-aspire-dashboard"
$image = "mcr.microsoft.com/dotnet/aspire-dashboard:13"

function Assert-Ok([string]$what) {
  if ($LASTEXITCODE -ne 0) {
    throw "$what failed (exit code $LASTEXITCODE)."
  }
}

Write-Host "Stopping/removing $containerName if it exists..." -ForegroundColor Cyan

# If container exists (running or stopped), remove it
$existingId = docker ps -a --filter "name=^/$containerName$" --format "{{.ID}}"
Assert-Ok "docker ps -a"

if ($existingId) {
  docker rm -f $containerName | Out-Null
  Assert-Ok "docker rm -f $containerName"
}

Write-Host "Pulling latest image: $image" -ForegroundColor Cyan
docker pull $image
Assert-Ok "docker pull $image"

Write-Host "Running $containerName..." -ForegroundColor Cyan
docker run `
  --name $containerName `
  -e DOTNET_DASHBOARD_UNSECURED_ALLOW_ANONYMOUS=true `
  -e ASPIRE_DASHBOARD_UNSECURED_ALLOW_ANONYMOUS=true `
  -e DASHBOARD__OTLP__CORS__ALLOWEDORIGINS=http://localhost:5173 `
  -e DASHBOARD__OTLP__CORS__ALLOWEDHEADERS=* `
  -p 18888:18888 `
  -p 4317:18889 `
  -p 4318:18890 `
  -d `
  $image | Out-Null
Assert-Ok "docker run $image"

Write-Host "Aspire Dashboard is running." -ForegroundColor Green
Write-Host "  UI:        http://localhost:18888"
Write-Host "  OTLP gRPC: localhost:4317"
Write-Host "  OTLP HTTP: http://localhost:4318/v1/traces"
Write-Host ""
Write-Host "Stop later with: docker rm -f $containerName"
