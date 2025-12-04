@echo off
REM Helper script untuk menjalankan Node C

echo ============================================================
echo Starting Node C - Attack Simulator
echo ============================================================
echo.

cd /d "%~dp0"
python nodes\node_c_attack.py

pause
