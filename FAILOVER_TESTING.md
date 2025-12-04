# Active-Passive Failover Testing Scenario

## Skenario: Node A Crash & Node B Backup

Skenario ini mendemonstrasikan **Active-Passive Failover** dimana:
- **Node A** = Primary sensor (bisa crash untuk testing)
- **Node B** = Backup sensor (auto-activate saat Node A down)
- **Data buffering** = Node B simpan data untuk sync ke Node A setelah recovery

---

## Cara Menjalankan

### 1. Start Broker A (Primary)
```bash
./start_broker_a.sh
```

### 2. Start Dashboard
```bash
python3 web/main.py
```
Dashboard: http://localhost:8000

### 3. Start Node A (Primary Sensor)
```bash
python3 nodes/node_a.py
```

### 4. Start Node B (Backup Sensor)
```bash
./start_node_b_failover.sh
```
atau
```bash
python3 nodes/node_b_failover.py
```

---

## Testing Failover

### Test 1: Simulate Node A Crash

1. **Di terminal Node A**, ketik:
   ```
   crash
   ```

2. **Yang terjadi:**
   - ❌ Node A akan publish event **"CRASHED"**
   - 🚨 Dashboard menampilkan **WARNING MERAH** di card Node A: "NODE A CRASHED!"
   - ✅ Node B mendeteksi crash → **AKTIVASI BACKUP MODE**
   - ⚠️ Dashboard menampilkan **WARNING KUNING** di card Node B: "BACKUP MODE ACTIVE!"
   - 📦 Node B mulai **buffer semua data** untuk sync nanti

3. **Monitor di dashboard:**
   - Node A card: **Status = CRASHED** (warna merah)
   - Node B card: **Mode = BACKUP** (warna kuning)
   - Node B card: **Buffered Messages** bertambah

### Test 2: Auto-Recovery Node A

1. **Tunggu 15 detik** → Node A akan auto-recovery

2. **Yang terjadi:**
   - ✅ Node A reconnect ke broker
   - 🔄 Node A publish event **"RECOVERY_COMPLETE"**
   - 💚 Dashboard menampilkan **INFO HIJAU** di card Node A: "PRIMARY NODE RECOVERED!"
   - 📤 Node B sync semua buffered data ke Node A
   - 📊 Dashboard Node B: **"DATA SYNC IN PROGRESS"**
   - 🔙 Node B kembali ke **EDGE COMPUTING MODE**

3. **Monitor di dashboard:**
   - Node A card: **Status = ACTIVE** (hijau)
   - Node B card: **Mode = EDGE** (normal)
   - Console Node B: "Data sync completed! X messages transferred."

### Test 3: Force Recovery (Manual)

Jika ingin recovery lebih cepat, di terminal Node A ketik:
```
recover
```

---

## Visual Indicators di Dashboard

### Node A (Primary Sensor)

**Normal:**
```
✅ Node A - Sensor
Status: ACTIVE
Current Broker: ✓ PRIMARY (Broker A)
Node Status: ✅ ACTIVE
```

**Crashed:**
```
🚨 NODE A CRASHED!
Primary sensor is DOWN. Waiting for Node B backup activation...

Status: 🚨 CRASHED
Node Status: 🚨 CRASHED
```

**Recovered:**
```
✅ PRIMARY NODE RECOVERED!
Node A is back online. Requesting data sync from backup...

Status: ACTIVE
Node Status: ✅ ACTIVE
```

### Node B (Backup Sensor)

**Normal (Edge Mode):**
```
✅ Node B - Edge Computing
Operation Mode: 🔧 EDGE
Node A Status: ✅ ACTIVE
```

**Backup Mode Active:**
```
⚠️ BACKUP MODE ACTIVE!
Node B is acting as primary sensor while Node A is down. Buffer: 45 messages

Operation Mode: ⚠️ BACKUP
Node A Status: 🚨 CRASHED
Buffered Messages: 45
```

**Data Sync:**
```
📤 DATA SYNC IN PROGRESS
Transferring 45 buffered messages to Node A...

Operation Mode: 🔧 EDGE
Node A Status: ✅ ACTIVE
```

---

## Commands untuk Node A

Di terminal Node A, tersedia commands:

| Command | Deskripsi |
|---------|-----------|
| `crash` | Simulasikan Node A crash (disconnect 15 detik) |
| `recover` | Force recovery segera (skip waiting) |
| `help` | Tampilkan command list |

---

## Metrics yang Dimonitor

### Node A (Primary)
- **Node Status**: ACTIVE / CRASHED
- **Failover Events**: Jumlah failover ke Broker B
- **Recovery Time**: Waktu recovery rata-rata
- **Success Rate**: Percentage pesan berhasil

### Node B (Backup)
- **Operation Mode**: EDGE / BACKUP
- **Node A Status**: ACTIVE / CRASHED
- **Buffered Messages**: Jumlah pesan di buffer (saat backup mode)
- **Offline Decisions**: Edge computing decisions

---

## Expected Behavior

1. **Crash Detection** (< 1 detik)
   - Node A publish "CRASHED" event
   - Dashboard langsung update status

2. **Backup Activation** (< 2 detik)
   - Node B terima alert dari system
   - Node B switch ke backup mode
   - Dashboard tampilkan warning

3. **Data Buffering** (selama Node A down)
   - Node B publish sensor data ke `/nodeA/data`
   - Semua data disimpan di `backup_data_buffer`
   - Buffer size maksimum: 500 messages

4. **Auto-Recovery** (15 detik sejak crash)
   - Node A reconnect
   - Publish "RECOVERY_COMPLETE"
   - Request data sync

5. **Data Sync** (< 5 detik)
   - Node B transfer semua buffered data
   - Publish ke `/nodeA/sync`
   - Clear buffer setelah sync

6. **Return to Normal** (< 3 detik)
   - Node B kembali ke edge mode
   - Dashboard update semua indicators
   - System kembali normal

---

## Troubleshooting

**Q: Node B tidak aktivasi backup mode?**
- Pastikan Node B subscribe ke `/system/alert`
- Check console Node B untuk errors
- Pastikan broker A running

**Q: Data sync tidak terjadi?**
- Check apakah buffer ada data (`len(backup_data_buffer)`)
- Lihat console Node B untuk sync messages
- Pastikan Node A sudah reconnect

**Q: Dashboard tidak update visual indicator?**
- Refresh browser (Ctrl+R)
- Check WebSocket connection (top-right corner)
- Lihat browser console (F12) untuk errors

**Q: Node A tidak auto-recovery?**
- Tunggu 15 detik penuh
- Atau ketik `recover` untuk force recovery
- Check broker A masih running

---

## Architecture Flow

```
NORMAL MODE:
Node A (Primary) ──> Broker A ──> Dashboard
Node B (Edge)    ──> Broker A ──> Dashboard

CRASH DETECTED:
Node A ──❌ CRASHED
         │
         └──> /system/alert {"event": "CRASHED"}
                      │
                      └──> Node B receives alert
                                   │
                                   └──> Activate BACKUP MODE

BACKUP MODE:
Node B (Backup) ──> Buffer + Publish ──> Dashboard (Shows warnings)

RECOVERY:
Node A ──✅ RECOVERED
         │
         └──> /system/alert {"event": "RECOVERY_COMPLETE"}
                      │
                      ├──> Node B syncs buffered data
                      │         │
                      │         └──> /nodeA/sync {buffered_data: [...]}
                      │
                      └──> Node B returns to EDGE MODE

NORMAL RESTORED:
Node A (Primary) ──> Broker A ──> Dashboard
Node B (Edge)    ──> Broker A ──> Dashboard
```

---

## Metrics untuk Presentasi UAS

1. **Crash Detection Time**: < 1 detik
2. **Backup Activation Time**: < 2 detik  
3. **Data Buffering**: 500 messages capacity
4. **Recovery Time**: ~15 detik (auto) atau instant (manual)
5. **Data Sync Time**: < 5 detik
6. **Zero Data Loss**: Semua data ter-buffer dan sync
7. **Visual Feedback**: Real-time dashboard updates dengan warning

---

**Dibuat untuk**: UAS Sistem Terdistribusi  
**Tim**: Aisha, Nada, Abdurrahman  
**Fitur**: Active-Passive Failover dengan Data Buffering & Sync
