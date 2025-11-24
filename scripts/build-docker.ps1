# PowerShell script to build and test Docker image for Bob LangGraph Agent

param(
    [string]$Tag = "latest",
    [switch]$NoBuildCache,
    [switch]$Push,
    [string]$Registry = ""
)

Write-Host "🐳 Building Bob LangGraph Agent Docker Image..." -ForegroundColor Cyan
Write-Host ""

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Host "❌ Error: Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  Warning: .env file not found. Creating from .env.example..." -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "📝 Please edit .env file and add your ANTHROPIC_API_KEY" -ForegroundColor Yellow
        exit 1
    } else {
        Write-Host "❌ Error: .env.example not found" -ForegroundColor Red
        exit 1
    }
}

# Build arguments
$BuildArgs = @()
if ($NoBuildCache) {
    $BuildArgs += "--no-cache"
}

$ImageName = "bob-langgraph-agent"
if ($Registry) {
    $ImageName = "$Registry/$ImageName"
}

# Build the image
Write-Host "🔨 Building image: ${ImageName}:${Tag}" -ForegroundColor Green
$BuildCommand = "docker build $($BuildArgs -join ' ') -t ${ImageName}:${Tag} ."

Write-Host "Running: $BuildCommand" -ForegroundColor Gray
Invoke-Expression $BuildCommand

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Build successful!" -ForegroundColor Green
Write-Host ""

# Tag as latest if not already
if ($Tag -ne "latest") {
    Write-Host "🏷️  Tagging as latest..." -ForegroundColor Cyan
    docker tag "${ImageName}:${Tag}" "${ImageName}:latest"
}

# Show image info
Write-Host "📊 Image Information:" -ForegroundColor Cyan
docker images $ImageName

# Test the image
Write-Host ""
Write-Host "🧪 Testing the image..." -ForegroundColor Cyan

# Check if container already exists
$ExistingContainer = docker ps -a --filter "name=bob-agent-test" --format "{{.Names}}"
if ($ExistingContainer) {
    Write-Host "Removing existing test container..." -ForegroundColor Yellow
    docker rm -f bob-agent-test | Out-Null
}

# Run test container
Write-Host "Starting test container..." -ForegroundColor Gray
docker run -d `
    --name bob-agent-test `
    -p 8001:8000 `
    --env-file .env `
    "${ImageName}:${Tag}"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start container" -ForegroundColor Red
    exit 1
}

# Wait for container to be healthy
Write-Host "Waiting for container to be ready..." -ForegroundColor Gray
$MaxWait = 30
$Waited = 0
$Healthy = $false

while ($Waited -lt $MaxWait) {
    Start-Sleep -Seconds 2
    $Waited += 2
    
    try {
        $Response = Invoke-WebRequest -Uri "http://localhost:8001/health" -UseBasicParsing -ErrorAction SilentlyContinue
        if ($Response.StatusCode -eq 200) {
            $Healthy = $true
            break
        }
    } catch {
        # Continue waiting
    }
    
    Write-Host "." -NoNewline -ForegroundColor Gray
}

Write-Host ""

if ($Healthy) {
    Write-Host "✅ Container is healthy!" -ForegroundColor Green
    
    # Test the API
    Write-Host ""
    Write-Host "🔍 Testing API endpoints..." -ForegroundColor Cyan
    
    try {
        $HealthResponse = Invoke-RestMethod -Uri "http://localhost:8001/health" -Method Get
        Write-Host "  ✓ Health check: $($HealthResponse.status)" -ForegroundColor Green
        Write-Host "  ✓ Model: $($HealthResponse.model)" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ Health check failed" -ForegroundColor Red
    }
    
    # Cleanup test container
    Write-Host ""
    Write-Host "🧹 Cleaning up test container..." -ForegroundColor Cyan
    docker stop bob-agent-test | Out-Null
    docker rm bob-agent-test | Out-Null
    
    Write-Host "✅ All tests passed!" -ForegroundColor Green
} else {
    Write-Host "❌ Container health check timeout" -ForegroundColor Red
    Write-Host ""
    Write-Host "Container logs:" -ForegroundColor Yellow
    docker logs bob-agent-test
    
    # Cleanup
    docker stop bob-agent-test | Out-Null
    docker rm bob-agent-test | Out-Null
    exit 1
}

# Push to registry if requested
if ($Push -and $Registry) {
    Write-Host ""
    Write-Host "📤 Pushing to registry: $Registry" -ForegroundColor Cyan
    docker push "${ImageName}:${Tag}"
    
    if ($Tag -ne "latest") {
        docker push "${ImageName}:latest"
    }
    
    Write-Host "✅ Push complete!" -ForegroundColor Green
}

Write-Host ""
Write-Host "🎉 Docker build complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To run the container:" -ForegroundColor Cyan
Write-Host "  docker-compose up -d" -ForegroundColor White
Write-Host ""
Write-Host "Or manually:" -ForegroundColor Cyan
Write-Host "  docker run -d -p 8000:8000 --env-file .env ${ImageName}:${Tag}" -ForegroundColor White
Write-Host ""
Write-Host "API documentation will be available at:" -ForegroundColor Cyan
Write-Host "  http://localhost:8000/docs" -ForegroundColor White
