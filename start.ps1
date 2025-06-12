# CloudCost AI Startup Script for Windows
Write-Host "🚀 Starting CloudCost AI..." -ForegroundColor Cyan

# Check if Python is installed
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Python not found. Please install Python 3.8+ and try again." -ForegroundColor Red
    exit 1
}

# Check if Node.js is installed
if (!(Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Node.js not found. Please install Node.js 16+ and try again." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Prerequisites check passed" -ForegroundColor Green

# Get current directory
$currentDir = Get-Location

# Start backend in background
Write-Host "🔧 Starting FastAPI backend..." -ForegroundColor Yellow
$backendCommand = "Set-Location '$currentDir\backend'; pip install -r requirements.txt; python main.py"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand

# Wait a moment for backend to start
Start-Sleep -Seconds 3

# Start frontend
Write-Host "🎨 Starting React frontend..." -ForegroundColor Yellow
$frontendCommand = "Set-Location '$currentDir\frontend'; npm install; npm start"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCommand

Write-Host "🎉 CloudCost AI is starting up!" -ForegroundColor Green
Write-Host "📊 Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "🔧 Backend API: http://localhost:8000" -ForegroundColor Cyan
Write-Host "📖 API Docs: http://localhost:8000/docs" -ForegroundColor Cyan

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 