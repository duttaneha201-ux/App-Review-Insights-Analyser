@echo off
echo Starting App Review Insights Servers...
echo.

echo Starting Backend API Server (port 8000)...
start "Backend API" cmd /k "python run_api_server.py"

timeout /t 3 /nobreak >nul

echo Starting Frontend Dev Server (port 3000)...
cd frontend
start "Frontend Dev" cmd /k "npm run dev"

echo.
echo ========================================
echo Servers starting...
echo ========================================
echo Backend API: http://localhost:8000
echo Frontend UI: http://localhost:3000
echo.
echo Press any key to exit (servers will continue running)...
pause >nul








