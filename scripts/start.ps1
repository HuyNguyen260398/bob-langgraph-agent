# PowerShell script to quickly start Bob LangGraph Agent

Write-Host "🚀 Starting Bob LangGraph Agent..." -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found!" -ForegroundColor Yellow
    
    if (Test-Path ".env.example") {
        Write-Host "Creating .env from .env.example..." -ForegroundColor Gray
        Copy-Item ".env.example" ".env"
        Write-Host ""
        Write-Host "📝 Please edit .env and add your ANTHROPIC_API_KEY:" -ForegroundColor Yellow
        Write-Host "   notepad .env" -ForegroundColor White
        Write-Host ""
        exit 1
    } else {
        Write-Host "❌ .env.example not found!" -ForegroundColor Red
        exit 1
    }
}

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Start services
Write-Host "🐳 Starting Docker containers..." -ForegroundColor Green
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to start services" -ForegroundColor Red
    exit 1
}

# Wait for service to be ready
Write-Host ""
Write-Host "⏳ Waiting for service to be ready..." -ForegroundColor Cyan

$MaxRetries = 12
$RetryCount = 0
$Healthy = $false

while ($RetryCount -lt $MaxRetries) {
    Start-Sleep -Seconds 5
    $RetryCount++
    
    try {
        $Response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -ErrorAction SilentlyContinue
        if ($Response.StatusCode -eq 200) {
            $Healthy = $true
            break
        }
    } catch {
        Write-Host "." -NoNewline -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host ""

if ($Healthy) {
    Write-Host "✅ Bob LangGraph Agent is running!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📝 Available endpoints:" -ForegroundColor Cyan
    Write-Host "  • API Documentation: " -NoNewline -ForegroundColor White
    Write-Host "http://localhost:8000/docs" -ForegroundColor Yellow
    Write-Host "  • Health Check:      " -NoNewline -ForegroundColor White
    Write-Host "http://localhost:8000/health" -ForegroundColor Yellow
    Write-Host "  • Chat API:          " -NoNewline -ForegroundColor White
    Write-Host "POST http://localhost:8000/chat" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "📊 Useful commands:" -ForegroundColor Cyan
    Write-Host "  • View logs:   " -NoNewline -ForegroundColor White
    Write-Host "docker-compose logs -f bob-agent" -ForegroundColor Gray
    Write-Host "  • Stop agent:  " -NoNewline -ForegroundColor White
    Write-Host "docker-compose down" -ForegroundColor Gray
    Write-Host "  • Restart:     " -NoNewline -ForegroundColor White
    Write-Host "docker-compose restart" -ForegroundColor Gray
    Write-Host ""
    Write-Host "🧪 Test the API:" -ForegroundColor Cyan
    Write-Host "  python test_api.py" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "❌ Service failed to start properly" -ForegroundColor Red
    Write-Host ""
    Write-Host "📋 Container logs:" -ForegroundColor Yellow
    docker-compose logs --tail=30 bob-agent
    Write-Host ""
    Write-Host "💡 Try checking:" -ForegroundColor Cyan
    Write-Host "  • Is your ANTHROPIC_API_KEY set in .env?" -ForegroundColor White
    Write-Host "  • Are all dependencies installed?" -ForegroundColor White
    Write-Host "  • Is port 8000 available?" -ForegroundColor White
    exit 1
}
