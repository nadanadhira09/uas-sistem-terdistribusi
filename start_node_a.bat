@echo off
REM Helper script untuk menjalankan Node A

echo ============================================================
echo Starting Node A - Fault-Tolerant Device
echo ============================================================
echo.

cd /d "%~dp0"
python nodes\node_a.py

pause
