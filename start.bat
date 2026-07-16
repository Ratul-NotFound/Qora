@echo off
echo ========================================================
echo       QORA RESEARCH AI - Startup Script
echo ========================================================

cd backend

echo [1/3] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH!
    pause
    exit /b
)

echo [2/3] Installing/Upgrading backend dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install dependencies!
    pause
    exit /b
)

echo [3/3] Starting QORA API Server...
start "" http://localhost:8000
echo.
echo ========================================================
echo   BACKEND IS RUNNING AT http://localhost:8000
echo ========================================================
echo.
echo Now open frontend\index.html in your web browser!
echo.
python main.py
pause
