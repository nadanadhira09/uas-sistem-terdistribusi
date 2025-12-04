@echo off
REM Helper script untuk menjalankan Node B

echo ============================================================
echo Starting Node B - Edge Processing Device
echo ============================================================
echo.

cd /d "%~dp0"
python nodes\node_b.py

pause
