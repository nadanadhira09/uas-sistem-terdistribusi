# 🏗️ Arsitektur Sistem

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        WEB DASHBOARD                            │
│                    (FastAPI + WebSocket)                        │
│                   http://localhost:8000                         │
└────────────────────┬────────────────────────────────────────────┘
                     │ Subscribe: /nodeA/*, /nodeB/*, /nodeC/*
                     │
┌────────────────────┴────────────────────────────────────────────┐
│                    MQTT BROKER LAYER                            │
│  ┌──────────────────┐              ┌──────────────────┐         │
│  │   Broker A       │◄────────────►│   Broker B       │         │
│  │   Port: 1883     │  (Backup)    │   Port: 1884     │         │
│  └──────────────────┘              └──────────────────┘         │
└────────┬───────────────────┬────────────────┬──────────────────┘
         │                   │                │
    ┌────┴────┐         ┌───┴────┐      ┌───┴─────┐
    │ Node A  │         │ Node B │      │ Node C  │
    │Failover │         │  Edge  │      │ Attack  │
    └─────────┘         └────────┘      └─────────┘
```

## Komponen Detail

### 1. MQTT Broker Layer

#### Broker A (Primary)

- **Port:** 1883
- **Role:** Primary MQTT broker
- **Config:** `brokers/brokerA.conf`
- **Data:** `brokers/data/brokerA/`
- **Features:**
  - Persistence enabled
  - Anonymous auth (development)
  - Unlimited connections

#### Broker B (Backup)

- **Port:** 1884
- **Role:** Backup/failover MQTT broker
- **Config:** `brokers/brokerB.conf`
- **Data:** `brokers/data/brokerB/`
- **Features:**
  - Same as Broker A
  - Activated on failover

### 2. IoT Devices Layer

#### Node A - Fault-Tolerant Device

**File:** `nodes/node_a.py`

**Threads:**

```
┌─────────────────────────────────┐
│         Node A Process          │
├─────────────────────────────────┤
│  Thread 1: Sensor Thread        │
│  - Generate sensor data         │
│  - Publish to /nodeA/data       │
│  - Interval: 2 seconds          │
├─────────────────────────────────┤
│  Thread 2: Health Check         │
│  - Monitor connection status    │
│  - Detect timeout (15s)         │
│  - Trigger failover/healing     │
│  - Interval: 5 seconds          │
└─────────────────────────────────┘
```

**State Machine:**

```
[Connected to A] ─┬─[Timeout]──►[Self-Healing]─┬─[Success]──►[Connected to A]
                  │                             │
                  └─[Failed]──►[Failover]───────┴─[Success]──►[Connected to B]
```

**Topics:**

- **Publish:** `/nodeA/data` (sensor data)
- **Publish:** `/nodeA/status` (events)

**Data Flow:**

```
Sensor → Queue → MQTT Client → Broker A/B → Dashboard
         ▲                         │
         └────[Health Check]───────┘
```

#### Node B - Edge Processing Device

**File:** `nodes/node_b.py`

**Threads:**

```
┌─────────────────────────────────┐
│         Node B Process          │
├─────────────────────────────────┤
│  Thread 1: Sensor + Processing  │
│  - Generate sensor data         │
│  - Edge processing (local)      │
│  - Statistics calculation       │
│  - Anomaly detection            │
│  - Decision making              │
│  - Interval: 3 seconds          │
├─────────────────────────────────┤
│  Thread 2: Status Monitor       │
│  - Check online/offline mode    │
│  - Report statistics            │
│  - Interval: 10 seconds         │
└─────────────────────────────────┘
```

**Operating Modes:**

```
[ONLINE MODE]                    [OFFLINE MODE]
     │                                │
     ├─ Sensor Reading                ├─ Sensor Reading
     ├─ Edge Processing               ├─ Edge Processing
     ├─ Local Decision                ├─ Local Decision
     └─ Publish to Broker             └─ Local Storage Only
           │                                │
     [Broker Available]             [Broker Unavailable]
           │                                │
           └──────[Connection Lost]────────┘
           ┌──────[Retry Success]───────────┐
           ▼                                 ▼
     [ONLINE MODE]                    [ONLINE MODE]
```

**Edge Processing Pipeline:**

```
Sensor Data → Buffer (100 samples)
                 │
                 ├─► Calculate Statistics (avg, min, max)
                 ├─► Anomaly Detection (threshold check)
                 ├─► Decision Making (alert, warning, normal)
                 └─► Action Determination (cooling, monitor, none)
```

**Topics:**

- **Publish:** `/nodeB/data` (processed data)
- **Publish:** `/nodeB/status` (events)

#### Node C - Attack Simulator

**File:** `nodes/node_c_attack.py`

**Attack Types:**

1. **Flood Attack**

```
┌────────────────────────────────┐
│   Flood Attack (10k msg/s)     │
├────────────────────────────────┤
│  Worker 1 ──► 1000 msg/s       │
│  Worker 2 ──► 1000 msg/s       │
│  Worker 3 ──► 1000 msg/s       │
│     ...                         │
│  Worker 10 ─► 1000 msg/s       │
└────────────────────────────────┘
    │
    └──► Total: 10,000 msg/s
```

2. **Topic Spam Attack**

```
Create 100+ unique topics:
/spam/1, /spam/2, ..., /spam/100
```

3. **Delayed ACK Attack**

```
Publish QoS 2 → Delay ACK (1s) → Consume resources
```

**Threads:**

```
┌─────────────────────────────────┐
│         Node C Process          │
├─────────────────────────────────┤
│  Main Thread: Menu & Control    │
├─────────────────────────────────┤
│  Thread 1-10: Flood Workers     │
│  Thread 11: Topic Spam          │
│  Thread 12: Delayed ACK         │
│  Thread 13: Statistics Monitor  │
└─────────────────────────────────┘
```

**Topics:**

- **Publish:** `/nodeC/attack_status` (status)
- **Publish:** `/attack/flood/*` (flood)
- **Publish:** `/spam/*` (spam)
- **Publish:** `/test/*` (delayed ACK)

### 3. Web Dashboard Layer

**File:** `web/main.py`

**Architecture:**

```
┌───────────────────────────────────────────┐
│          FastAPI Application              │
├───────────────────────────────────────────┤
│  HTTP Routes:                             │
│  - GET /                                  │
│  - GET /dashboard                         │
│  - GET /api/data                          │
├───────────────────────────────────────────┤
│  WebSocket:                               │
│  - /ws (bidirectional communication)      │
├───────────────────────────────────────────┤
│  MQTT Client:                             │
│  - Subscribe: /nodeA/*, /nodeB/*, /nodeC/*│
│  - On message: Broadcast to WebSockets    │
└───────────────────────────────────────────┘
```

**Data Flow:**

```
MQTT Broker
    │
    ├─► on_message() callback
    │       │
    │       ├─► Update dashboard_data
    │       └─► broadcast_update()
    │               │
    │               └─► Send to all WebSocket clients
    │
WebSocket Clients (Browsers)
    │
    └─► Update UI real-time
```

**Frontend Architecture:**

```
dashboard.html
    │
    ├─► HTML Structure
    │   - Header
    │   - Node A Card
    │   - Node B Card
    │   - Node C Card
    │   - Statistics Card
    │
    └─► dashboard.js
        │
        ├─► WebSocket Connection
        ├─► Event Handlers
        ├─► UI Update Functions
        └─► Chart.js Integration
```

## Data Flow Diagram

### Normal Operation

```
┌──────────┐         ┌──────────┐         ┌───────────┐
│ Node A   │────────►│ Broker A │────────►│ Dashboard │
└──────────┘  pub    └──────────┘   sub   └───────────┘
                                              ▲
┌──────────┐                                  │
│ Node B   │──────────────────────────────────┘
└──────────┘  pub
```

### Failover Scenario

```
┌──────────┐         ┌──────────┐ [X Down]
│ Node A   │─────X──►│ Broker A │
└──────────┘         └──────────┘
     │
     │ [Failover]
     │
     ▼              ┌──────────┐         ┌───────────┐
     └─────────────►│ Broker B │────────►│ Dashboard │
                    └──────────┘         └───────────┘
```

### Attack Scenario

```
┌──────────┐
│ Node C   │────► [10,000 msg/s]
└──────────┘          │
                      ▼
              ┌──────────┐
              │ Broker A │─────► [Stress Test]
              └──────────┘
                      │
                      ▼
              ┌───────────┐
              │ Dashboard │─────► [Monitoring]
              └───────────┘
```

## Performance Characteristics

### Node A

- **Publish Rate:** 0.5 msg/s (every 2 seconds)
- **Health Check:** Every 5 seconds
- **Failover Time:** ~2-3 seconds
- **Recovery Time:** ~2-5 seconds

### Node B

- **Processing Rate:** 0.33 msg/s (every 3 seconds)
- **Buffer Size:** 100 samples
- **Processing Latency:** <10ms (local)
- **Offline Tolerance:** Unlimited (local processing)

### Node C

- **Max Flood Rate:** 10,000 msg/s
- **Workers:** 10 parallel threads
- **Topic Creation:** 100 topics in ~1 second
- **Memory Impact:** ~100MB during full attack

### Dashboard

- **WebSocket Latency:** <50ms
- **Update Rate:** Real-time (event-driven)
- **Max Clients:** 100+ concurrent connections
- **Chart Update:** Every message (throttled)

## Security Considerations

### Current Implementation (Development)

- ⚠️ Anonymous authentication enabled
- ⚠️ No TLS/SSL encryption
- ⚠️ No rate limiting
- ⚠️ No input validation

### Production Recommendations

- ✅ Enable MQTT authentication (username/password)
- ✅ Use TLS/SSL for encryption
- ✅ Implement rate limiting
- ✅ Add input validation
- ✅ Use ACL for topic permissions
- ✅ Enable audit logging

## Scalability

### Current Setup

- **Nodes:** 3 devices
- **Brokers:** 2 instances
- **Messages:** ~1-10k/s (attack mode)

### Scaling Options

1. **Horizontal Scaling:**

   - Add more Node A/B instances
   - Use broker clustering
   - Deploy multiple dashboard instances

2. **Vertical Scaling:**

   - Increase broker resources
   - Optimize message size
   - Batch processing

3. **Cloud Deployment:**
   - AWS IoT Core
   - Azure IoT Hub
   - Google Cloud IoT

## Technology Stack

### Backend

- **Python 3.8+**
- **Paho MQTT Client** (MQTT communication)
- **FastAPI** (Web framework)
- **Uvicorn** (ASGI server)
- **WebSockets** (Real-time updates)

### Frontend

- **HTML5**
- **Vanilla JavaScript** (No frameworks)
- **Chart.js** (Data visualization)
- **WebSocket API** (Real-time connection)

### Infrastructure

- **Mosquitto MQTT Broker** (Message broker)
- **Windows OS** (Development environment)

## Monitoring & Debugging

### Logs Location

```
Terminal 1: Broker A logs (stdout)
Terminal 2: Broker B logs (stdout)
Terminal 3: Dashboard logs (uvicorn)
Terminal 4: Node A logs (stdout)
Terminal 5: Node B logs (stdout)
Terminal 6: Node C logs (stdout)
```

### Key Metrics

- Message throughput (msg/s)
- Connection status (up/down)
- Failover count
- Offline decisions
- Attack statistics

### Debug Tools

- Browser DevTools (F12) for WebSocket
- MQTT Explorer for topic inspection
- Wireshark for network analysis

---

**Designed for:** IoT learning, fault tolerance demonstration, stress testing
