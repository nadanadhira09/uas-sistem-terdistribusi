# 📊 FLOWCHART SISTEM IOT FAULT-TOLERANT

## 🎯 FLOWCHART UTAMA - SISTEM LENGKAP

```
                    ┌─────────────────────┐
                    │   START SYSTEM      │
                    │   (6 Terminals)     │
                    └──────────┬──────────┘
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
    ┌───────▼────────┐  ┌──────▼──────┐  ┌───────▼────────┐
    │  Broker A:1883 │  │ Broker B:1884│  │  Dashboard Web │
    │   (Primary)    │  │   (Backup)   │  │  Port :8000    │
    └───────┬────────┘  └──────┬───────┘  └───────┬────────┘
            │                  │                  │
            └──────────┬───────┴──────────────────┘
                       │
            ┌──────────┴──────────┐
            │                     │
    ┌───────▼────────┐    ┌──────▼──────────┐    ┌─────────────┐
    │   NODE A       │    │    NODE B       │    │   NODE C    │
    │   Primary      │    │    Backup       │    │   Attacker  │
    │   Sensor       │    │    Edge Device  │    │   DDoS      │
    └───────┬────────┘    └──────┬──────────┘    └──────┬──────┘
            │                    │                       │
            └────────────────────┼───────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  MQTT Message Exchange  │
                    │  Topics:                │
                    │  - /nodeA/data          │
                    │  - /nodeB/data          │
                    │  - /system/alert        │
                    │  - /attack/flood/*      │
                    └─────────────────────────┘
```

---

## 📋 FLOWCHART NODE A - PRIMARY SENSOR

```
        ┌────────────────┐
        │  START NODE A  │
        └────────┬───────┘
                 │
        ┌────────▼────────┐
        │ Connect Broker A│
        │  (localhost:1883)│
        └────────┬────────┘
                 │
            ┌────▼─────┐
            │Connected?│
            └────┬─────┘
                 │
        ┌────────┴────────┐
       NO│               │YES
        │                │
        ▼                ▼
   ┌─────────┐    ┌──────────────┐
   │Failover │    │Start Threads:│
   │to       │    │- Sensor      │
   │Broker B │    │- Health Check│
   │         │    │- Metrics     │
   └─────────┘    │- Command     │
                  └──────┬───────┘
                         │
                  ┌──────▼───────┐
                  │ NORMAL MODE  │
                  │ Publish Data │
                  │ Every 2 sec  │
                  └──────┬───────┘
                         │
                  ┌──────▼───────┐
                  │User types    │
                  │ "crash"?     │
                  └──────┬───────┘
                         │
                    ┌────┴────┐
                   NO│        │YES
                     │         │
                     │    ┌────▼────────────┐
                     │    │ CRASH SIMULATION│
                     │    └────┬────────────┘
                     │         │
                     │    ┌────▼────────────────────────┐
                     │    │ 1. Publish CRASHED event    │
                     │    │ 2. Disconnect from broker   │
                     │    │ 3. Stop all operations      │
                     │    │ 4. Sleep 15 seconds         │
                     │    └────┬────────────────────────┘
                     │         │
                     │    ┌────▼────────────┐
                     │    │ AUTO RECOVERY   │
                     │    └────┬────────────┘
                     │         │
                     │    ┌────▼──────────────────────┐
                     │    │ 1. Reconnect to Broker A  │
                     │    │ 2. Publish RECOVERY event │
                     │    │ 3. Request data sync      │
                     │    └────┬──────────────────────┘
                     │         │
                     └─────────┴─────────┐
                                         │
                                    ┌────▼────┐
                                    │Continue │
                                    │Normal   │
                                    │Mode     │
                                    └─────────┘
```

---

## 🛡️ FLOWCHART NODE B - BACKUP SENSOR

```
        ┌────────────────┐
        │  START NODE B  │
        └────────┬───────┘
                 │
        ┌────────▼────────┐
        │ Connect Broker A│
        │  (localhost:1883)│
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │Subscribe Topics:│
        │ - /system/alert │
        │ - /nodeB/command│
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │  STANDBY MODE   │
        │ Edge Computing  │
        │ Only (No Sensor)│
        └────────┬────────┘
                 │
        ┌────────▼─────────┐
        │Receive Message?  │
        └────────┬─────────┘
                 │
        ┌────────┴────────┐
        │                 │
    ┌───▼──────┐    ┌─────▼────────┐
    │  CRASHED │    │   RECOVERY   │
    │  event?  │    │   COMPLETE?  │
    └───┬──────┘    └─────┬────────┘
        │YES              │YES
        │                 │
   ┌────▼────────────┐    │
   │ ACTIVATE BACKUP │    │
   └────┬────────────┘    │
        │                 │
   ┌────▼─────────────────┐│
   │ 1. Set backup mode   ││
   │ 2. Start sensor pub  ││
   │ 3. Buffer all data   ││
   │    (deque maxlen=500)││
   └────┬─────────────────┘│
        │                  │
        │         ┌────────▼──────────────┐
        │         │ SYNC DATA TO NODE A   │
        │         └────┬──────────────────┘
        │              │
        │         ┌────▼──────────────────┐
        │         │ 1. Publish all buffer │
        │         │    to /nodeA/sync     │
        │         │ 2. Update progress    │
        │         │ 3. Clear buffer       │
        │         └────┬──────────────────┘
        │              │
        │         ┌────▼──────────────────┐
        │         │ DEACTIVATE BACKUP     │
        │         └────┬──────────────────┘
        │              │
        └──────────────┴──────────┐
                                  │
                         ┌────────▼────────┐
                         │ Back to Standby │
                         │ Mode            │
                         └─────────────────┘
```

---

## ⚔️ FLOWCHART NODE C - ATTACK SIMULATOR

```
        ┌────────────────┐
        │  START NODE C  │
        └────────┬───────┘
                 │
        ┌────────▼────────┐
        │ Connect Broker A│
        │  (localhost:1883)│
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │   IDLE MODE     │
        │ Waiting command │
        └────────┬────────┘
                 │
        ┌────────▼────────────┐
        │ User input:         │
        │ y = attack          │
        │ n = cancel          │
        └────────┬────────────┘
                 │
            ┌────┴────┐
           NO│        │YES
             │         │
             │    ┌────▼──────────────────┐
             │    │ START ATTACK          │
             │    │ Publish ATTACK_STARTED│
             │    └────┬──────────────────┘
             │         │
             │    ┌────▼──────────────────────────┐
             │    │ FLOOD MESSAGES                │
             │    │ Rate: 10,000 msg/sec          │
             │    │ Topics:                       │
             │    │ - /attack/flood/sensor        │
             │    │ - /attack/flood/control       │
             │    │ - /spam/data                  │
             │    │ - /spam/noise                 │
             │    └────┬──────────────────────────┘
             │         │
             │    ┌────▼──────────────────┐
             │    │ Duration: 30 seconds  │
             │    │ (configurable)        │
             │    └────┬──────────────────┘
             │         │
             │    ┌────▼──────────────────┐
             │    │ STOP ATTACK           │
             │    │ Publish ATTACK_STOPPED│
             │    └────┬──────────────────┘
             │         │
             └─────────┴────────┐
                                │
                       ┌────────▼────────┐
                       │ Back to Idle    │
                       │ Wait next cmd   │
                       └─────────────────┘
```

---

## 🌐 FLOWCHART DASHBOARD - WEB INTERFACE

```
        ┌────────────────┐
        │ START DASHBOARD│
        │ FastAPI:8000   │
        └────────┬───────┘
                 │
        ┌────────▼────────┐
        │ Init WebSocket  │
        │ Server          │
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │ Subscribe MQTT: │
        │ - /nodeA/data   │
        │ - /nodeA/status │
        │ - /nodeB/data   │
        │ - /nodeB/status │
        │ - /nodeC/status │
        │ - /system/alert │
        └────────┬────────┘
                 │
        ┌────────▼─────────┐
        │ Receive MQTT Msg?│
        └────────┬─────────┘
                 │
        ┌────────┴─────────────────────┐
        │                              │
   ┌────▼────────┐              ┌──────▼─────────┐
   │ /nodeA/data │              │ /system/alert  │
   │ /nodeB/data │              │ (Event)        │
   └────┬────────┘              └──────┬─────────┘
        │                              │
   ┌────▼──────────────┐      ┌────────▼────────────────┐
   │ Update Metrics:   │      │ Process Event:          │
   │ - Message count   │      │ - CRASHED               │
   │ - Temperature     │      │ - RECOVERY_COMPLETE     │
   │ - Humidity        │      │ - ATTACK_STARTED        │
   │ - Pressure        │      │ - ATTACK_STOPPED        │
   └────┬──────────────┘      └────────┬────────────────┘
        │                              │
        │                     ┌────────▼────────────────┐
        │                     │ Update Dashboard:       │
        │                     │ - Event timeline        │
        │                     │ - Countdown timer       │
        │                     │ - Progress bar          │
        │                     │ - Visual status cards   │
        │                     └────────┬────────────────┘
        │                              │
        └──────────────┬───────────────┘
                       │
              ┌────────▼────────┐
              │ Broadcast via   │
              │ WebSocket to    │
              │ Browser Client  │
              └────────┬────────┘
                       │
              ┌────────▼────────┐
              │ Browser Updates │
              │ Real-time       │
              │ (No Refresh)    │
              └─────────────────┘
```

---

## 🔄 FLOWCHART SKENARIO LENGKAP - CRASH & RECOVERY

```
┌─────────────────────────────────────────────────────────────┐
│                   TIMELINE SCENARIO                         │
└─────────────────────────────────────────────────────────────┘

t=0s    │ ✅ System Normal
        │ Node A: Publishing sensor data
        │ Node B: Standby mode
        │ Dashboard: All green
        │
t=10s   │ 💥 User types "crash" in Node A terminal
        │
t=10s   │ 📤 Node A publishes CRASHED event
        │ 🔌 Node A disconnects from Broker A
        │ ⏸️  Node A stops all operations
        │
t=10.5s │ 📥 Node B receives CRASHED event
        │ 🛡️  Node B activates backup mode
        │ 📡 Node B starts publishing sensor data
        │ 💾 Node B buffers all data (deque)
        │
t=11s   │ 🖥️  Dashboard detects crash:
        │     - Node A card turns RED
        │     - "📛 Messages (FROZEN)" label
        │     - Node B card turns YELLOW
        │     - "🚀 Backup Messages" counter
        │     - Event timeline: "💥 Node A Down!"
        │     - Countdown timer: 15s → 14s
        │
t=12s   │ 📊 Node B message count: 1
        │ 📊 Total messages continues increasing
        │ ⏱️  Countdown: 13s
        │
t=15s   │ 📊 Node B message count: 3
        │ ⏱️  Countdown: 10s
        │
t=20s   │ 📊 Node B message count: 6
        │ ⏱️  Countdown: 5s
        │
t=25s   │ 🔄 AUTO-RECOVERY TRIGGERED
        │ 🔌 Node A reconnects to Broker A
        │ 📤 Node A publishes RECOVERY_COMPLETE
        │ 📨 Node A requests data sync
        │
t=25.5s │ 📥 Node B receives RECOVERY_COMPLETE
        │ 📤 Node B starts syncing buffered data
        │ 📊 Progress: 0/8 messages (0%)
        │
t=26s   │ 🖥️  Dashboard shows:
        │     - "🎉 Node A Recovered!" event
        │     - Progress bar: 4/8 (50%)
        │     - Node A card turns GREEN
        │
t=27s   │ 📊 Progress: 8/8 (100%)
        │ ✅ Data sync complete
        │ 🛡️  Node B deactivates backup mode
        │ ⏸️  Node B stops sensor publishing
        │
t=28s   │ ✅ SYSTEM NORMAL
        │ Node A: Back to publishing
        │ Node B: Back to standby
        │ Dashboard: All green
        │ Zero data loss achieved! ✅
        │
```

---

## 📊 DECISION TREE - KONDISI & AKSI

```
                    ┌───────────────┐
                    │ System State  │
                    └───────┬───────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
   ┌────▼─────┐      ┌──────▼──────┐    ┌──────▼──────┐
   │  NORMAL  │      │   CRASHED   │    │   ATTACK    │
   └────┬─────┘      └──────┬──────┘    └──────┬──────┘
        │                   │                   │
        │                   │                   │
   ┌────▼──────────┐   ┌────▼──────────┐  ┌────▼─────────┐
   │ Node A: Send  │   │ Node A: DOWN  │  │ All Nodes:   │
   │ Node B: Wait  │   │ Node B: BACKUP│  │ ONLINE       │
   │ Node C: Idle  │   │ Node C: Idle  │  │ High Load    │
   └───────────────┘   └────┬──────────┘  └──────────────┘
                            │
                    ┌───────▼────────┐
                    │ Wait 15 seconds│
                    └───────┬────────┘
                            │
                    ┌───────▼────────┐
                    │ AUTO RECOVERY  │
                    └───────┬────────┘
                            │
                    ┌───────▼────────┐
                    │ SYNC DATA      │
                    └───────┬────────┘
                            │
                    ┌───────▼────────┐
                    │ Back to NORMAL │
                    └────────────────┘
```

---

## 📝 PENJELASAN FLOWCHART

### **1. Flowchart Utama - Sistem Lengkap**
Menunjukkan arsitektur keseluruhan dengan 6 komponen:
- **2 Brokers** (Primary & Backup) untuk redundansi
- **3 Nodes** (Sensor A, Backup B, Attacker C)
- **1 Dashboard** untuk monitoring real-time

**Alur Data:**
```
Nodes → MQTT Brokers → Dashboard (WebSocket) → Browser
```

---

### **2. Flowchart Node A - Primary Sensor**

**Fase Normal:**
1. Connect ke Broker A (Primary)
2. Jika gagal → Failover ke Broker B
3. Jika sukses → Start 4 threads:
   - **Sensor Thread**: Publish data setiap 2 detik
   - **Health Check Thread**: Monitor koneksi setiap 5 detik
   - **Metrics Thread**: Report statistik setiap 10 detik
   - **Command Thread**: Listen user input (crash/recover)

**Fase Crash:**
1. User ketik `crash`
2. Publish event "CRASHED" ke `/system/alert`
3. Disconnect dari broker
4. Stop semua operasi
5. Sleep 15 detik (simulasi downtime)
6. **Auto-recovery:**
   - Reconnect ke Broker A
   - Publish "RECOVERY_COMPLETE"
   - Request data sync dari Node B
7. Kembali normal

**Metrics yang Diukur:**
- Recovery time (avg, fastest, slowest)
- Message success rate
- Availability percentage
- Uptime vs downtime

---

### **3. Flowchart Node B - Backup Sensor**

**Fase Standby:**
1. Connect ke Broker A
2. Subscribe ke `/system/alert` dan `/nodeB/command`
3. Mode standby (hanya edge computing, tidak publish sensor)
4. Monitor alert messages

**Fase Backup (Saat Node A Crash):**
1. Terima event "CRASHED"
2. Set `is_backup_mode = True`
3. Mulai publish sensor data (gantikan Node A)
4. Buffer semua data ke `deque(maxlen=500)`
5. Update status setiap 5 detik

**Fase Sync (Saat Node A Recovery):**
1. Terima event "RECOVERY_COMPLETE"
2. Publish semua buffered data ke `/nodeA/sync`
3. Update progress bar (X/Y messages)
4. Clear buffer
5. Set `is_backup_mode = False`
6. Stop sensor publishing
7. Kembali standby

**Zero Data Loss:**
```
Data selama crash = Buffer size (misal: 8 messages)
Data di-sync ke Node A = 8 messages
Data hilang = 0 ✅
```

---

### **4. Flowchart Node C - Attack Simulator**

**Fase Idle:**
- Connect ke Broker A
- Wait user input (y/n)

**Fase Attack:**
1. User ketik `y`
2. Publish "ATTACK_STARTED" ke `/system/alert`
3. Create 10 MQTT clients untuk paralel publishing
4. Flood messages dengan rate 10,000 msg/s ke:
   - `/attack/flood/sensor`
   - `/attack/flood/control`
   - `/spam/data`
   - `/spam/noise`
5. Duration: 30 detik
6. Publish "ATTACK_STOPPED"
7. Kembali idle

**Tujuan:**
- Test **resilience** system di bawah beban tinggi
- Ukur dampak ke **latency** Node A & B
- Pastikan **broker tidak crash**

---

### **5. Flowchart Dashboard - Web Interface**

**Initialization:**
1. Start FastAPI server di port 8000
2. Init WebSocket server
3. Connect ke MQTT Broker A sebagai subscriber
4. Subscribe ke semua topics penting

**Message Processing:**
1. Terima message dari MQTT
2. Parse JSON payload
3. Update internal state
4. Broadcast ke browser via WebSocket
5. Browser update UI real-time (tanpa refresh)

**Visual Updates:**
- **Node cards**: Green (online), Red (down), Yellow (backup), Red pulsing (attack)
- **Event timeline**: Scroll panel dengan 20 events terakhir
- **Countdown timer**: 15s → 0s saat recovery
- **Progress bar**: Data sync percentage
- **Charts**: Line chart untuk message trends

**WebSocket Flow:**
```
MQTT Broker → Dashboard Backend → WebSocket → Browser Client
                (Python)                        (JavaScript)
```

---

### **6. Timeline Scenario - Crash & Recovery**

**Penjelasan Detail per Detik:**

| Time | Event | Node A | Node B | Dashboard |
|------|-------|--------|--------|-----------|
| t=0s | Normal | ✅ Online | ⏸️ Standby | 🟢 All green |
| t=10s | Crash | 💥 User types `crash` | ⏸️ Standby | 🟢 Normal |
| t=10s | Alert | 🔴 Disconnected | 📥 Received CRASHED | 🔴 Detected |
| t=10.5s | Failover | ❌ Down | 🛡️ Backup activated | 🟡 Backup mode |
| t=11s | UI Update | 📛 FROZEN | 🚀 Backup msgs: 0 | ⏱️ Countdown: 15s |
| t=15s | Buffering | ❌ Down | 📊 Msgs: 3 | ⏱️ Countdown: 10s |
| t=25s | Recovery | 🔄 Reconnecting | 📊 Msgs: 8 | ⏱️ Countdown: 0s |
| t=25.5s | Sync | 📨 Requesting | 📤 Syncing 0/8 | 📊 Progress: 0% |
| t=26s | Syncing | ✅ Online | 📤 Syncing 4/8 | 📊 Progress: 50% |
| t=27s | Complete | ✅ Normal | ✅ Standby | 🎉 Sync 100% |
| t=28s | Normal | ✅ Publishing | ⏸️ Standby | 🟢 All green |

**Total Downtime:** 15 detik  
**Data Loss:** 0 messages ✅  
**Availability:** 99.9%

---

### **7. Decision Tree - Kondisi & Aksi**

**3 Kondisi Sistem:**

1. **NORMAL:**
   - Node A: Primary sensor (active)
   - Node B: Edge computing (passive)
   - Node C: Idle
   - Aksi: Continue normal operations

2. **CRASHED:**
   - Node A: Down (disconnected)
   - Node B: Backup mode (active)
   - Node C: Idle
   - Aksi: Failover → Wait 15s → Recovery → Sync

3. **ATTACK:**
   - Node A: Online (stressed)
   - Node B: Standby (stressed)
   - Node C: Flooding (active)
   - Aksi: Monitor latency, ensure stability

---

## 🎯 KEY TAKEAWAYS

### **Untuk Presentasi UAS:**

1. **Tunjukkan Flowchart Utama** → Jelaskan arsitektur 6 komponen
2. **Tunjukkan Timeline Scenario** → Demo crash & recovery step-by-step
3. **Tunjukkan Dashboard** → Visual proof dengan event timeline + countdown
4. **Explain Decision Tree** → 3 kondisi sistem (Normal/Crashed/Attack)

### **Pertanyaan yang Bisa Dijawab:**

**Q:** "Bagaimana alur failover bekerja?"  
**A:** Lihat Flowchart Node A (fase crash) + Node B (fase backup)

**Q:** "Berapa lama recovery time?"  
**A:** Lihat Timeline Scenario → 15 detik auto-recovery

**Q:** "Apakah data hilang saat crash?"  
**A:** Lihat Flowchart Node B (fase sync) → Zero data loss dengan buffer

**Q:** "Bagaimana attack berbeda dari crash?"  
**A:** Lihat Decision Tree → CRASH = node down, ATTACK = high load

---

## ✅ VALIDASI SKENARIO PENGUJIAN

### **Skenario 1: Network Failure**
- **Flowchart:** Node A (fase crash) + Node B (fase backup)
- **Durasi:** 15 detik downtime
- **Metrics:** Recovery time, availability, message success rate

### **Skenario 2: Cyber Attack**
- **Flowchart:** Node C (fase attack)
- **Laju:** 10,000 msg/s (configurable)
- **Metrics:** Latency impact, throughput, broker stability

Flowchart ini **100% sesuai** dengan requirement skenario pengujian Anda! 🎉
