# 🔧 Troubleshooting Guide

## Common Issues & Solutions

### 1. Broker Issues

#### ❌ Error: "Address already in use"

**Problem:** Port 1883 atau 1884 sudah digunakan oleh proses lain.

**Solution:**

```powershell
# Cek proses yang menggunakan port
netstat -ano | findstr :1883
netstat -ano | findstr :1884

# Kill proses (ganti <PID> dengan nomor PID dari output di atas)
taskkill /PID <PID> /F

# Atau stop service Mosquitto jika terinstall sebagai service
net stop mosquitto
```

#### ❌ Error: "Error loading config file"

**Problem:** File konfigurasi tidak ditemukan atau path salah.

**Solution:**

```powershell
# Pastikan Anda di folder yang benar
cd C:\iot-fault-tolerant-sim

# Verifikasi file ada
dir brokers\brokerA.conf
dir brokers\brokerB.conf

# Jalankan dengan path absolut
mosquitto -c C:\iot-fault-tolerant-sim\brokers\brokerA.conf
```

#### ❌ Error: "Error: Unable to open persistence database"

**Problem:** Folder data persistence tidak ada.

**Solution:**

```powershell
# Buat folder yang diperlukan
mkdir brokers\data\brokerA
mkdir brokers\data\brokerB

# Atau jalankan setup.bat
setup.bat
```

### 2. Python/Dependencies Issues

#### ❌ Error: "ModuleNotFoundError: No module named 'paho'"

**Problem:** Library paho-mqtt tidak terinstall.

**Solution:**

```powershell
# Install semua dependencies
pip install -r requirements.txt

# Atau install manual
pip install paho-mqtt fastapi uvicorn websockets

# Jika masih error, upgrade pip dulu
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### ❌ Error: "ImportError: No module named 'fastapi'"

**Problem:** FastAPI tidak terinstall atau Python environment salah.

**Solution:**

```powershell
# Cek Python version
python --version  # Harus 3.8+

# Install FastAPI dan dependencies
pip install fastapi uvicorn[standard]

# Jika menggunakan virtual environment
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

#### ❌ Error: "Python is not recognized"

**Problem:** Python tidak ada di PATH.

**Solution:**

1. Install Python dari python.org
2. Centang "Add Python to PATH" saat install
3. Atau tambah manual ke PATH:
   - Buka System Properties → Environment Variables
   - Tambahkan `C:\Python3x` ke PATH

### 3. Node Connection Issues

#### ❌ Node A/B: "Connection refused"

**Problem:** Broker tidak running atau port salah.

**Solution:**

```powershell
# 1. Pastikan broker running
# Cek di terminal broker apakah ada output

# 2. Test koneksi dengan mosquitto_pub
mosquitto_pub -h localhost -p 1883 -t test -m "hello"

# 3. Cek firewall
# Windows Firewall → Allow app → Pilih Python & Mosquitto

# 4. Restart broker
# Ctrl+C di terminal broker, lalu start ulang
```

#### ❌ Node A: "Failover loop"

**Problem:** Kedua broker down atau tidak accessible.

**Solution:**

```powershell
# 1. Pastikan minimal 1 broker running
start_broker_a.bat  # Terminal baru

# 2. Cek log Node A apakah ada error spesifik

# 3. Restart Node A
# Ctrl+C, lalu start ulang
```

#### ❌ Node B: "Stuck in offline mode"

**Problem:** Broker down atau retry logic bermasalah.

**Solution:**

```powershell
# 1. Start broker jika belum
start_broker_a.bat

# 2. Tunggu 10-30 detik (retry dengan exponential backoff)

# 3. Jika masih offline, restart Node B
# Ctrl+C di terminal Node B
start_node_b.bat
```

### 4. Dashboard Issues

#### ❌ Error: "Address already in use" (port 8000)

**Problem:** Port 8000 sudah digunakan.

**Solution:**

```powershell
# Opsi 1: Kill proses yang menggunakan port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Opsi 2: Ubah port di web/main.py
# Edit baris terakhir:
uvicorn.run(app, host="0.0.0.0", port=8001)  # Ganti 8000 → 8001

# Lalu akses di: http://localhost:8001/dashboard
```

#### ❌ Dashboard: "WebSocket Disconnected"

**Problem:** Koneksi WebSocket gagal atau server down.

**Solution:**

```powershell
# 1. Refresh browser (Ctrl+F5)

# 2. Cek browser console (F12) untuk error detail

# 3. Restart dashboard server
# Ctrl+C di terminal dashboard
start_dashboard.bat

# 4. Cek browser console apakah ada error CORS
# Jika ada, akses dengan http:// bukan https://
```

#### ❌ Dashboard: "Page not loading"

**Problem:** Template tidak ditemukan atau path salah.

**Solution:**

```powershell
# Verifikasi file template ada
dir web\templates\dashboard.html
dir web\static\dashboard.js

# Jika tidak ada, buat ulang folder
mkdir web\templates
mkdir web\static

# Copy file template dan static
# (pastikan file ada dari project source)
```

#### ❌ Dashboard: "Chart not showing"

**Problem:** Chart.js tidak load atau JavaScript error.

**Solution:**

1. **Cek koneksi internet** (Chart.js load dari CDN)
2. **Buka browser console (F12)** untuk lihat error
3. **Refresh page** (Ctrl+F5)
4. **Clear browser cache**
5. **Coba browser lain** (Chrome/Edge/Firefox)

### 5. Attack/Node C Issues

#### ❌ Node C: "Attack not working"

**Problem:** Broker overload atau connection limit.

**Solution:**

```powershell
# 1. Kurangi attack rate
# Edit nodes/node_c_attack.py:
self.flood_rate = 1000  # Dari 10000 → 1000

# 2. Kurangi jumlah workers
self.num_threads = 5  # Dari 10 → 5

# 3. Restart broker untuk clear connection
# Ctrl+C di broker, lalu start ulang
```

#### ❌ Node C: "Menu tidak muncul"

**Problem:** Input stream error atau terminal issue.

**Solution:**

```powershell
# 1. Gunakan PowerShell (bukan CMD)

# 2. Atau jalankan langsung dari Python
python nodes\node_c_attack.py

# 3. Jika tetap error, edit script untuk auto-attack:
# Di node_c_attack.py, tambahkan di fungsi start():
# self.start_attack("flood")  # Auto start tanpa menu
```

### 6. Performance Issues

#### 🐌 Dashboard slow/laggy

**Problem:** Terlalu banyak message atau browser overload.

**Solution:**

```powershell
# 1. Stop attack Node C jika sedang berjalan

# 2. Reduce publishing rate di nodes
# Edit node_a.py:
time.sleep(5)  # Dari 2 → 5 detik

# Edit node_b.py:
time.sleep(10)  # Dari 3 → 10 detik

# 3. Restart nodes dengan rate baru
```

#### 🐌 High CPU usage

**Problem:** Flood attack terlalu agresif.

**Solution:**

```powershell
# 1. Stop Node C attack

# 2. Reduce flood rate
# Edit nodes/node_c_attack.py:
self.flood_rate = 100  # Test dengan rate lebih rendah

# 3. Monitor CPU dengan Task Manager
```

#### 🐌 High memory usage

**Problem:** Message buffer terlalu besar atau memory leak.

**Solution:**

```powershell
# 1. Restart semua komponen

# 2. Reduce buffer size di Node B
# Edit nodes/node_b.py:
self.sensor_buffer = deque(maxlen=20)  # Dari 100 → 20

# 3. Monitor memory dengan Task Manager
```

### 7. Windows-Specific Issues

#### ❌ "Permission denied" errors

**Problem:** Insufficient permissions.

**Solution:**

```powershell
# 1. Run PowerShell as Administrator
# Right-click PowerShell → Run as Administrator

# 2. Atau ubah execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### ❌ Batch file tidak bisa dijalankan

**Problem:** Execution policy atau antivirus blocking.

**Solution:**

```powershell
# 1. Right-click batch file → Run as Administrator

# 2. Atau jalankan manual command di dalamnya

# 3. Check antivirus dan add exception untuk folder project
```

#### ❌ Mosquitto service conflict

**Problem:** Mosquitto terinstall sebagai Windows service.

**Solution:**

```powershell
# Stop service
net stop mosquitto

# Disable auto-start
sc config mosquitto start= disabled

# Atau uninstall service
mosquitto uninstall
```

## Diagnostic Commands

### Check System Status

```powershell
# Check Python
python --version
pip list | findstr mqtt
pip list | findstr fastapi

# Check Mosquitto
mosquitto -h
where mosquitto

# Check ports
netstat -ano | findstr :1883
netstat -ano | findstr :1884
netstat -ano | findstr :8000

# Check processes
tasklist | findstr python
tasklist | findstr mosquitto
```

### Test MQTT Connection

```powershell
# Subscribe test (Terminal 1)
mosquitto_sub -h localhost -p 1883 -t test/#

# Publish test (Terminal 2)
mosquitto_pub -h localhost -p 1883 -t test/hello -m "Testing MQTT"

# Jika berhasil, message akan muncul di Terminal 1
```

### Test Dashboard API

```powershell
# Test HTTP endpoint
curl http://localhost:8000/api/data

# Atau buka di browser:
# http://localhost:8000/api/data
# Harus return JSON data
```

## Logging & Debugging

### Enable Verbose Logging

**Broker (mosquitto):**

```powershell
# Edit brokers/brokerA.conf, tambahkan:
log_type all
log_type debug

# Restart broker
```

**Python Nodes:**

```python
# Tambahkan di awal file node_*.py:
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Monitor in Real-Time

```powershell
# Terminal 1: Watch logs
Get-Content -Path "broker.log" -Wait

# Terminal 2: Monitor connections
mosquitto_sub -h localhost -p 1883 -t '$SYS/#' -v
```

## Recovery Procedures

### Full System Reset

```powershell
# 1. Stop all components (Ctrl+C di semua terminal)

# 2. Clean data
del /Q brokers\data\brokerA\*
del /Q brokers\data\brokerB\*

# 3. Start fresh
start_broker_a.bat
start_broker_b.bat
start_dashboard.bat
start_node_a.bat
start_node_b.bat
```

### Reset Specific Component

**Reset Broker:**

```powershell
# Stop broker (Ctrl+C)
# Delete data
del /Q brokers\data\brokerA\*
# Start again
start_broker_a.bat
```

**Reset Node:**

```powershell
# Stop node (Ctrl+C)
# Start again
start_node_a.bat
```

**Reset Dashboard:**

```powershell
# Stop dashboard (Ctrl+C)
# Clear browser cache
# Start again
start_dashboard.bat
```

## Getting Help

### Log Files to Check

1. **Broker logs** → Terminal output
2. **Node logs** → Terminal output
3. **Dashboard logs** → Terminal output + browser console
4. **System logs** → Windows Event Viewer

### Debug Checklist

- [ ] Semua prerequisites terinstall?
- [ ] Semua dependencies Python terinstall?
- [ ] Port 1883, 1884, 8000 available?
- [ ] Firewall tidak blocking?
- [ ] Broker running?
- [ ] Python version 3.8+?
- [ ] Internet connection (untuk Chart.js CDN)?

### Contact Information

Jika masih ada masalah:

1. Capture **screenshot** error
2. Copy **full error message** dari terminal
3. Note **steps to reproduce**
4. Check **ARCHITECTURE.md** untuk detail sistem

---

**Pro Tip:** Selalu cek terminal output untuk error detail. 90% masalah terdeteksi di sana! 🔍
