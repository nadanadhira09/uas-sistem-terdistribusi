@echo off
REM Helper script untuk menjalankan Web Dashboard

echo ============================================================
echo Starting Web Dashboard Server
echo ============================================================
echo Dashboard will be available at: http://localhost:8000/dashboard
echo.

cd /d "%~dp0"
python web\main.py

pause
