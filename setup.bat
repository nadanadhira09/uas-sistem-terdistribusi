@echo off
REM Setup script untuk membuat folder yang diperlukan dan install dependencies

echo ============================================================
echo IoT Fault-Tolerant Simulation - Setup
echo ============================================================
echo.

cd /d "%~dp0"

echo Creating required directories...
if not exist "brokers\data\brokerA\" mkdir brokers\data\brokerA
if not exist "brokers\data\brokerB\" mkdir brokers\data\brokerB
if not exist "web\static\" mkdir web\static
if not exist "web\templates\" mkdir web\templates

echo.
echo Directories created successfully!
echo.

echo Installing Python dependencies...
pip install -r requirements.txt

echo.
echo ============================================================
echo Setup completed!
echo ============================================================
echo.
echo You can now start the components:
echo 1. start_broker_a.bat
echo 2. start_broker_b.bat
echo 3. start_dashboard.bat
echo 4. start_node_a.bat
echo 5. start_node_b.bat
echo 6. start_node_c.bat
echo.
echo Open http://localhost:8000/dashboard in your browser
echo ============================================================

pause
