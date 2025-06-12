Write-Host "🚀 CloudCost AI - Simple Startup" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python not found. Install Python 3.8+ and try again." -ForegroundColor Red
    exit 1
}

if (!(Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Node.js not found. Install Node.js 16+ and try again." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Prerequisites OK" -ForegroundColor Green
Write-Host ""

# Install backend dependencies
Write-Host "📦 Installing backend dependencies..." -ForegroundColor Yellow
Set-Location backend
pip install -q fastapi uvicorn boto3 pydantic
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install backend dependencies" -ForegroundColor Red
    exit 1
}
Set-Location ..

Write-Host "✅ Backend dependencies installed" -ForegroundColor Green
Write-Host ""

# Install frontend dependencies
Write-Host "📦 Installing frontend dependencies..." -ForegroundColor Yellow
Set-Location frontend
npm install --silent
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install frontend dependencies" -ForegroundColor Red
    exit 1
}
Set-Location ..

Write-Host "✅ Frontend dependencies installed" -ForegroundColor Green
Write-Host ""

Write-Host "🎉 Setup complete! Now starting services..." -ForegroundColor Green
Write-Host ""

# Start backend
Write-Host "🔧 Starting backend (FastAPI)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python main.py" -WindowStyle Normal

Start-Sleep -Seconds 2

# Start frontend
Write-Host "🎨 Starting frontend (React)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm start" -WindowStyle Normal

Write-Host ""
Write-Host "🎊 CloudCost AI is starting!" -ForegroundColor Green
Write-Host ""
Write-Host "📱 Dashboard:    http://localhost:3000" -ForegroundColor Cyan
Write-Host "🔧 Backend API:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "📚 API Docs:     http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "⌛ Please wait a moment for both services to fully start..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Press Enter to continue..." -ForegroundColor White
Read-Host 