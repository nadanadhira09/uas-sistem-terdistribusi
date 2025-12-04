# 📊 Dashboard Guide - IoT Fault-Tolerant System

## 🎯 Overview
Dashboard ini menampilkan seluruh proses failover secara visual dan informatif. Semua event ditampilkan dalam **Event Timeline** dengan notifikasi real-time.

## 🎨 Visual Indicators

### Node Status Cards

#### 1️⃣ **Node Online (Hijau)**
```
╔════════════════════════════════╗
║  ✅                            ║ <- 64px emoji
║  ONLINE                        ║ <- Status besar
║  System operational            ║
╠════════════════════════════════╣
║  Border: Hijau (#10b981)       ║
║  Background: Gradient hijau    ║
╚════════════════════════════════╝
```

#### 2️⃣ **Node Down (Merah - Pulsing)**
```
╔════════════════════════════════╗
║  💥                            ║ <- Animated
║  NODE DOWN                     ║ <- Merah tebal
║  Primary sensor crashed        ║
╠════════════════════════════════╣
║  Border: Merah (#dc2626)       ║
║  Animation: Pulse 2s infinite  ║
╚════════════════════════════════╝
```

#### 3️⃣ **Backup Mode (Kuning)**
```
╔════════════════════════════════╗
║  🛡️                            ║
║  BACKUP MODE                   ║ <- Kuning tebal
║  Operating as primary sensor   ║
╠════════════════════════════════╣
║  Border: Kuning (#f59e0b)      ║
║  Background: Gradient kuning   ║
╚════════════════════════════════╝
```

#### 4️⃣ **Attacking (Merah Pulsing)**
```
╔════════════════════════════════╗
║  ⚔️                            ║ <- Animated
║  ATTACKING                     ║ <- Merah tebal
║  10,000 msg/s                  ║
╠════════════════════════════════╣
║  Border: Merah (#dc2626)       ║
║  Animation: PulseAttack 1s     ║
╚════════════════════════════════╝
```

---

## 📋 Event Timeline

Event Timeline menampilkan semua notifikasi sistem secara berurutan (terbaru di atas):

### Event Types:

#### ✅ **Node Online Events (Hijau)**
```
┌──────────────────────────────────────────┐
│ ✅  Node A Online                        │ 14:30:01
│     Primary sensor is now active         │
│                                          │
└──────────────────────────────────────────┘
```

#### 💥 **Node Crashed Events (Merah)**
```
┌──────────────────────────────────────────┐
│ 💥  Node A Down!                         │ 14:32:15
│     Primary sensor has crashed!          │
│     Backup system should activate        │
└──────────────────────────────────────────┘
```

#### 🛡️ **Backup Activation (Kuning)**
```
┌──────────────────────────────────────────┐
│ 🛡️  Node B Backup Activated!            │ 14:32:16
│     Node B is now operating as primary   │
│     sensor backup                        │
└──────────────────────────────────────────┘
```

#### ⏱️ **Recovery Countdown (Biru)**
```
┌──────────────────────────────────────────┐
│ ⏱️  Node A Auto-Recovery in Progress    │ 14:32:16
│     Recovery countdown: ⏲️ 15s           │ <- Update real-time
│                                          │
└──────────────────────────────────────────┘
```

#### 🎉 **Node Recovered (Hijau)**
```
┌──────────────────────────────────────────┐
│ 🎉  Node A Recovered!                    │ 14:32:31
│     Primary sensor is back online and    │
│     operational                          │
└──────────────────────────────────────────┘
```

#### 📤 **Data Sync Progress (Ungu)**
```
┌──────────────────────────────────────────┐
│ 📤  Data Sync in Progress               │ 14:32:32
│     Transferring buffered data from      │
│     Node B to Node A: 8/8 messages       │
│     ████████████████████ 100%            │ <- Progress bar
└──────────────────────────────────────────┘
```

#### ⚔️ **Attack Started (Merah)**
```
┌──────────────────────────────────────────┐
│ ⚔️  Attack Started!                      │ 14:35:00
│     Node C is sending 10,000 msg/sec     │
│     to test system resilience            │
└──────────────────────────────────────────┘
```

---

## 🎬 Complete Scenario Flow

### **Skenario Lengkap yang Terlihat di Dashboard:**

```
Step 1: System Startup
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Event Timeline:
  ✅ Node A Online - Primary sensor is now active
  ✅ Node B Online - Backup sensor / Edge processor is ready
  ✅ Node C Online - Attack simulation node is ready

Node Cards:
  [Node A: ✅ ONLINE - Green border]
  [Node B: ✅ ONLINE - Green border]
  [Node C: ✅ ONLINE - Green border]


Step 2: Attack Simulation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Event Timeline:
  ⚔️ Attack Started! - Sending 10,000 msg/sec

Node Cards:
  [Node A: ✅ ONLINE - Green border]
  [Node B: ✅ ONLINE - Green border]
  [Node C: ⚔️ ATTACKING - Red pulsing border]


Step 3: Node A Crash
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Event Timeline:
  💥 Node A Down! - Primary sensor has crashed!
  ⏱️ Recovery countdown: 15s (counting down)

Node Cards:
  [Node A: 💥 NODE DOWN - Red pulsing border]
  [Node B: ✅ ONLINE - Green border]
  [Node C: ⚔️ ATTACKING - Red pulsing border]


Step 4: Node B Backup Activation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Event Timeline:
  🛡️ Node B Backup Activated! - Now operating as primary
  ⏱️ Recovery countdown: 12s (counting down)
  💥 Node A Down!

Node Cards:
  [Node A: 💥 NODE DOWN - Red pulsing border]
  [Node B: 🛡️ BACKUP MODE - Yellow border]
  [Node C: ⚔️ ATTACKING - Red pulsing border]


Step 5: Countdown (Real-time)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Event Timeline:
  ⏱️ Recovery countdown: 8s (updating setiap detik)
  🛡️ Node B Backup Activated!
  💥 Node A Down!

Timer updates: 15s → 14s → 13s → ... → 1s → 0s


Step 6: Node A Recovery
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Event Timeline:
  🎉 Node A Recovered! - Primary sensor is back online
  🛡️ Node B Backup Activated!
  💥 Node A Down!

Node Cards:
  [Node A: ✅ ONLINE - Green border]
  [Node B: 🛡️ BACKUP MODE - Yellow border]
  [Node C: ⚔️ ATTACKING - Red pulsing border]


Step 7: Data Sync
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Event Timeline:
  📤 Data Sync in Progress - Transferring 8/8 messages
      ████████████████████ 100%
  🎉 Node A Recovered!
  🛡️ Node B Backup Activated!

Progress bar animates from 0% to 100%


Step 8: System Normal
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Event Timeline:
  ✅ Data Sync Complete - Successfully transferred 8 messages
  🔙 Node B Normal Mode - Returned to edge computing
  📤 Data Sync in Progress
  🎉 Node A Recovered!

Node Cards:
  [Node A: ✅ ONLINE - Green border]
  [Node B: ✅ ONLINE - Green border]
  [Node C: ⚔️ ATTACKING - Red pulsing border]
```

---

## 🖥️ Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│  🌐 IoT Fault-Tolerant Dashboard          [Connected]      │
│  Real-time monitoring with advanced metrics                 │
├─────────────────────────────────────────────────────────────┤
│  Total Msg   Msg/Sec   Latency   Active Nodes   Uptime     │
│   12,450      1,234     2.3ms         3          00:05:23   │
├─────────────────────────────────────────────────────────────┤
│  📋 Event Timeline & Notifications         [Clear Log]      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ✅ Data Sync Complete - 8 messages      14:32:34   │   │
│  │ 🔙 Node B Normal Mode                   14:32:33   │   │
│  │ 📤 Data Sync Progress: 8/8 ████ 100%   14:32:32   │   │
│  │ 🎉 Node A Recovered!                    14:32:31   │   │
│  │ 🛡️ Node B Backup Activated!            14:32:16   │   │
│  │ 💥 Node A Down!                         14:32:15   │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  ✅          │  │  🛡️          │  │  ⚔️          │     │
│  │  ONLINE      │  │ BACKUP MODE  │  │  ATTACKING   │     │
│  │ System OK    │  │ Primary role │  │  10K msg/s   │     │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤     │
│  │ 📡 NODE A    │  │ 🔧 NODE B    │  │ ⚔️ NODE C    │     │
│  │ [ONLINE]     │  │ [ONLINE]     │  │ [ATTACKING]  │     │
│  │              │  │              │  │              │     │
│  │ Broker: A    │  │ Backup: ON   │  │ Rate: 10K/s  │     │
│  │ Failover: 0  │  │ Buffer: 8    │  │ Duration: 5s │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Testing Steps

### **Untuk Menjalankan Skenario Lengkap:**

1. **Start All Components** (6 terminals):
   ```bash
   Terminal 1: mosquitto -c brokers/brokerA.conf
   Terminal 2: mosquitto -c brokers/brokerB.conf
   Terminal 3: python web/main.py
   Terminal 4: python nodes/node_a.py
   Terminal 5: python nodes/node_b_failover.py
   Terminal 6: python nodes/node_c_attack.py
   ```

2. **Open Dashboard**:
   - Browser: http://localhost:8000
   - Lihat: 3 node muncul dengan status hijau (ONLINE)

3. **Simulate Node C Attack** (Terminal 6):
   - Tekan `y` untuk start attack
   - Lihat: Node C card berubah merah pulsing
   - Timeline: "⚔️ Attack Started!"

4. **Simulate Node A Crash** (Terminal 4):
   - Ketik: `crash`
   - Lihat di Dashboard:
     - Node A card: 💥 NODE DOWN (merah pulsing)
     - Timeline: "💥 Node A Down!"
     - Countdown: "⏱️ Recovery countdown: 15s"
     - Node B card: 🛡️ BACKUP MODE (kuning)
     - Timeline: "🛡️ Node B Backup Activated!"

5. **Wait for Auto-Recovery** (15 detik):
   - Lihat countdown: 15s → 14s → ... → 1s → 0s
   - Node A otomatis recovery
   - Lihat di Dashboard:
     - Node A card: ✅ ONLINE (hijau)
     - Timeline: "🎉 Node A Recovered!"
     - Progress bar: "📤 Data Sync in Progress"
     - Timeline: "✅ Data Sync Complete - 8 messages"
     - Node B card: ✅ ONLINE (hijau)
     - Timeline: "🔙 Node B Normal Mode"

6. **Verify Normal Operation**:
   - Semua node hijau
   - Timeline menunjukkan complete flow
   - Metrics kembali normal

---

## 🎨 Color Scheme Reference

| Status | Border Color | Background | Animation |
|--------|--------------|------------|-----------|
| Online | `#10b981` (Green) | Gradient hijau | None |
| Down | `#dc2626` (Red) | Gradient merah | Pulse 2s |
| Backup | `#f59e0b` (Yellow) | Gradient kuning | None |
| Attacking | `#dc2626` (Red) | Gradient merah | PulseAttack 1s |

---

## ✨ Features

### ✅ Implemented:
- [x] Event Timeline dengan scroll
- [x] Big status indicators (64px emoji)
- [x] Animated borders per status
- [x] Real-time countdown timer (15s)
- [x] Data sync progress bar
- [x] Auto-notification untuk semua event
- [x] Color-coded visual indicators
- [x] Clear log button
- [x] Responsive layout

### 📊 Metrics Displayed:
- Total messages
- Messages per second
- Average latency
- Active nodes count
- System uptime
- Failover events
- Buffer size (Node B)
- Attack rate (Node C)
- Success rates

---

## 🔧 Customization

### Mengubah Countdown Duration:
```python
# File: nodes/node_a.py
self.crash_recovery_time = 15  # Ubah ke nilai lain (detik)
```

### Mengubah Buffer Size:
```python
# File: nodes/node_b_failover.py
self.backup_data_buffer = deque(maxlen=500)  # Ubah max size
```

### Mengubah Attack Rate:
```python
# File: nodes/node_c_attack.py
self.attack_rate = 10000  # Messages per second
```

---

## 📝 Notes

- **Timeline**: Menyimpan max 20 events terakhir
- **Countdown**: Update setiap 1 detik
- **Progress Bar**: Smooth animation 0.3s
- **WebSocket**: Auto-reconnect setiap 3 detik jika disconnect
- **Charts**: Update real-time setiap data baru

---

## 🎓 Untuk Presentasi UAS

### **Highlight Points:**

1. **Visual Clarity**: 
   - Semua proses terlihat jelas di dashboard
   - Tidak perlu melihat terminal

2. **Real-time Updates**:
   - Event muncul instant
   - Countdown live
   - Progress bar animated

3. **Professional Design**:
   - Modern gradient colors
   - Smooth animations
   - Responsive layout

4. **Complete Monitoring**:
   - 10 tahap skenario terlihat jelas
   - Timeline history
   - Metrics lengkap

---

**Dashboard Ready for UAS Presentation! 🎉**
