@echo off
REM Helper script untuk menjalankan Broker A

echo ============================================================
echo Starting Mosquitto Broker A (Port 1883)
echo ============================================================
echo.

cd /d "%~dp0"
mosquitto -c brokers\brokerA.conf

pause
