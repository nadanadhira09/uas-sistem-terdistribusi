@echo off
REM Helper script untuk menjalankan Broker B

echo ============================================================
echo Starting Mosquitto Broker B (Port 1884)
echo ============================================================
echo.

cd /d "%~dp0"
mosquitto -c brokers\brokerB.conf

pause
