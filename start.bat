@echo off
echo 🚀 CloudCost AI - Starting Application...
echo.

echo ✅ Installing backend dependencies...
cd backend
pip install fastapi uvicorn boto3 pydantic
cd ..

echo ✅ Installing frontend dependencies...
cd frontend
call npm install
cd ..

echo.
echo 🎉 Dependencies installed! Starting services...
echo.

echo 🔧 Starting FastAPI backend on port 8000...
start "CloudCost Backend" cmd /k "cd backend && python main.py"

timeout /t 3 /nobreak >nul

echo 🎨 Starting React frontend on port 3000...
start "CloudCost Frontend" cmd /k "cd frontend && npm start"

echo.
echo 🎊 CloudCost AI is starting!
echo.
echo 📱 Dashboard:    http://localhost:3000
echo 🔧 Backend API:  http://localhost:8000
echo 📚 API Docs:     http://localhost:8000/docs
echo.
echo ⌛ Please wait for both services to start...
echo.
pause 