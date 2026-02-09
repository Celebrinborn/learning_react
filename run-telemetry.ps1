<#
Kill/remove existing container (if present), pull latest image, then run Jaeger all-in-one.

Exposes:
- OTLP gRPC  : localhost:4317  (Python backend)
- OTLP HTTP : localhost:4318  (Browser frontend)
- Jaeger UI : http://localhost:16686
#>

$ErrorActionPreference = "Stop"

$containerName = "otel-jaeger"
$image = "jaegertracing/all-in-one:latest"

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
  -e COLLECTOR_OTLP_ENABLED=true `
  -p 16686:16686 `
  -p 4317:4317 `
  -p 4318:4318 `
  -d `
  $image | Out-Null
Assert-Ok "docker run $image"

Write-Host "Jaeger is running." -ForegroundColor Green
Write-Host "  UI:        http://localhost:16686"
Write-Host "  OTLP gRPC:  http://localhost:4317"
Write-Host "  OTLP HTTP: http://localhost:4318/v1/traces"
Write-Host ""
Write-Host "Stop later with: docker rm -f $containerName"
