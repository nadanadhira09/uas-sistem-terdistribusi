"""
Web Dashboard - FastAPI + WebSocket untuk monitoring realtime (IMPROVED VERSION)
Fitur Baru:
- Dynamic node management (add/remove nodes)
- Advanced metrics tracking
- Communication flow monitoring
- System health analytics
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import paho.mqtt.client as mqtt
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
import uvicorn
from pathlib import Path
from collections import deque
import time

app = FastAPI(title="IoT Fault-Tolerant Dashboard (Improved)")

# Mount static files
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# WebSocket connections
active_connections: List[WebSocket] = []

# Dynamic node registry
registered_nodes = {}

# Data storage with improved metrics
dashboard_data = {
    "nodes": {},  # Dynamic nodes storage
    "system_metrics": {
        "total_messages_received": 0,
        "messages_per_second": 0,
        "avg_system_latency": 0,
        "total_uptime": 0,
        "uptime_start": datetime.now().isoformat(),
        "communication_flow": {
            "broker_a_messages": 0,
            "broker_b_messages": 0,
            "total_throughput": 0
        }
    },
    "attack_resilience": {
        "attacks_handled": 0,
        "messages_during_attack": 0,
        "system_degradation": 0,
        "recovery_success_rate": 100.0
    }
}

# Message rate tracking
message_timestamps = deque(maxlen=1000)
latencies = deque(maxlen=500)

# MQTT Client
mqtt_client = None

class NodeRegistration(BaseModel):
    """Model for dynamic node registration"""
    node_id: str
    node_type: str  # 'sensor', 'edge', 'attacker'
    description: Optional[str] = None

def init_node_data(node_id: str, node_type: str):
    """Initialize data structure for a new node"""
    return {
        "id": node_id,
        "type": node_type,
        "status": "unknown",
        "last_update": None,
        "data_count": 0,
        "latest_data": {},
        "metrics": {
            "messages_sent": 0,
            "messages_failed": 0,
            "success_rate": 100.0,
            "avg_latency": 0
        },
        "registered_at": datetime.now().isoformat()
    }

def on_connect(client, userdata, flags, rc):
    """MQTT on connect callback"""
    if rc == 0:
        print("[Dashboard] ✅ Connected to MQTT broker")
        # Subscribe to all relevant topics
        client.subscribe("/+/data")
        client.subscribe("/+/status")
        client.subscribe("/+/metrics")
        client.subscribe("/+/attack_status")  # For Node C attack status
        client.subscribe("/+/attack_metrics")  # For Node C attack metrics
        client.subscribe("/attack/#")
        client.subscribe("/spam/#")
        print("[Dashboard] 📡 Subscribed to all topics")
    else:
        print(f"[Dashboard] ❌ Connection failed with code {rc}")

def on_message(client, userdata, msg):
    """MQTT on message callback"""
    try:
        # Track message rate
        message_timestamps.append(time.time())
        
        payload = json.loads(msg.payload.decode())
        topic = msg.topic
        
        # Extract node ID from topic dengan logic yang lebih baik
        if topic.startswith('/attack/') or topic.startswith('/spam/'):
            # Attack topics dari Node C
            node_id = 'nodeC'
        elif '/' in topic:
            # Normal topics: /nodeA/data, /nodeB/status, etc
            node_id = topic.split('/')[1]
        else:
            node_id = 'unknown'
        
        # Auto-register node if not exists
        if node_id not in dashboard_data["nodes"]:
            node_type = detect_node_type(node_id, topic, payload)
            dashboard_data["nodes"][node_id] = init_node_data(node_id, node_type)
            print(f"[Dashboard] 🆕 Auto-registered node: {node_id} (type: {node_type})")
        
        # Update dashboard data
        update_dashboard_data(topic, payload, node_id)
        
        # Calculate system metrics
        update_system_metrics()
        
        # Broadcast to all websocket connections
        asyncio.run(broadcast_update(topic, payload))
        
    except Exception as e:
        print(f"[Dashboard] ❌ Error processing message: {e}")

def detect_node_type(node_id: str, topic: str, payload: dict) -> str:
    """Auto-detect node type from messages"""
    if 'attack' in topic.lower() or node_id.lower().startswith('nodec'):
        return 'attacker'
    elif 'edge' in str(payload).lower() or node_id.lower().startswith('nodeb'):
        return 'edge'
    else:
        return 'sensor'

def update_dashboard_data(topic: str, payload: dict, node_id: str):
    """Update internal dashboard data with improved tracking"""
    now = datetime.now().isoformat()
    
    dashboard_data["system_metrics"]["total_messages_received"] += 1
    
    # Update node-specific data
    if node_id in dashboard_data["nodes"]:
        node_data = dashboard_data["nodes"][node_id]
        
        if "/data" in topic:
            node_data["latest_data"] = payload
            node_data["data_count"] += 1
            node_data["last_update"] = now
            
            # Track latency if available
            if "send_time" in payload:
                latency = time.time() - payload["send_time"]
                latencies.append(latency)
                node_data["metrics"]["avg_latency"] = latency
            
            # Track broker usage
            if "broker" in payload:
                broker_key = f"broker_{payload['broker'].lower()}_messages"
                if broker_key in dashboard_data["system_metrics"]["communication_flow"]:
                    dashboard_data["system_metrics"]["communication_flow"][broker_key] += 1
        
        elif "/status" in topic or "/attack_status" in topic:
            node_data["status"] = payload.get("event", payload.get("status", "unknown"))
            node_data["last_update"] = now
            
            # Copy relevant status info
            for key in ["broker", "mode", "failover_count", "reconnect_count", 
                       "offline_decisions", "retry_count", "details", 
                       "total_messages", "messages_per_second", "attack_duration",
                       "is_primary_active", "event", "is_backup_mode", "node_a_status",
                       "data_count"]:
                if key in payload:
                    node_data[key] = payload[key]
            
            # Handle backup buffer size from backup_data_buffer length
            if "message" in payload and "buffered" in payload["message"].lower():
                # Extract buffer size from message like "buffer: 123 messages"
                import re
                match = re.search(r'(\d+)\s+buffered', payload["message"])
                if match:
                    node_data["buffer_size"] = int(match.group(1))
        
        elif "/metrics" in topic or "/attack_metrics" in topic:
            # Merge metrics data
            if "metrics" not in node_data:
                node_data["metrics"] = {}
            
            # Update from various metric types
            if "recovery_metrics" in payload:
                node_data["recovery_metrics"] = payload["recovery_metrics"]
            if "message_metrics" in payload:
                node_data["metrics"].update(payload["message_metrics"])
            if "communication_metrics" in payload:
                node_data["metrics"].update(payload["communication_metrics"])
            if "attack_performance" in payload:
                node_data["attack_metrics"] = payload["attack_performance"]
                
                # Update attack resilience metrics
                dashboard_data["attack_resilience"]["attacks_handled"] += 1
                if payload["attack_performance"].get("messages_sent", 0) > 0:
                    dashboard_data["attack_resilience"]["messages_during_attack"] += \
                        payload["attack_performance"]["messages_sent"]
            
            node_data["last_update"] = now
        
        elif topic.startswith("/attack/") or topic.startswith("/spam/"):
            # Count attack messages
            if node_id in dashboard_data["nodes"]:
                dashboard_data["nodes"][node_id]["data_count"] = \
                    dashboard_data["nodes"][node_id].get("data_count", 0) + 1

def update_system_metrics():
    """Calculate and update system-wide metrics"""
    # Calculate messages per second
    now = time.time()
    recent_messages = sum(1 for ts in message_timestamps if now - ts <= 1.0)
    dashboard_data["system_metrics"]["messages_per_second"] = recent_messages
    
    # Calculate average system latency
    if latencies:
        dashboard_data["system_metrics"]["avg_system_latency"] = \
            round(sum(latencies) / len(latencies) * 1000, 2)  # ms
    
    # Calculate total throughput
    dashboard_data["system_metrics"]["communication_flow"]["total_throughput"] = recent_messages
    
    # Calculate uptime
    start_time = datetime.fromisoformat(dashboard_data["system_metrics"]["uptime_start"])
    uptime_seconds = (datetime.now() - start_time).total_seconds()
    dashboard_data["system_metrics"]["total_uptime"] = round(uptime_seconds, 2)

async def broadcast_update(topic: str, payload: dict):
    """Broadcast update to all connected websockets"""
    message = {
        "type": "mqtt_update",
        "topic": topic,
        "payload": payload,
        "dashboard_data": dashboard_data,
        "timestamp": datetime.now().isoformat()
    }
    
    disconnected = []
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except:
            disconnected.append(connection)
    
    # Remove disconnected connections
    for conn in disconnected:
        if conn in active_connections:
            active_connections.remove(conn)

def start_mqtt_client():
    """Start MQTT client"""
    global mqtt_client
    
    mqtt_client = mqtt.Client(
        client_id=f"dashboard_{int(datetime.now().timestamp())}",
        callback_api_version=mqtt.CallbackAPIVersion.VERSION1
    )
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    
    try:
        mqtt_client.connect("localhost", 1883, keepalive=60)
        mqtt_client.loop_start()
        print("[Dashboard] 🚀 MQTT client started")
    except Exception as e:
        print(f"[Dashboard] ❌ Failed to connect to MQTT broker: {e}")

@app.on_event("startup")
async def startup_event():
    """Startup event"""
    print("=" * 70)
    print("IoT Fault-Tolerant Dashboard Server (IMPROVED)")
    print("=" * 70)
    print("\n📊 New Features:")
    print("  - Dynamic node management")
    print("  - Advanced metrics tracking")
    print("  - Communication flow monitoring")
    print("  - Attack resilience analytics\n")
    start_mqtt_client()

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event"""
    print("[Dashboard] 🛑 Shutting down...")
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "IoT Fault-Tolerant Dashboard API (Improved)",
        "dashboard": "/dashboard",
        "api": {
            "data": "/api/data",
            "nodes": "/api/nodes",
            "register": "/api/nodes/register",
            "metrics": "/api/metrics"
        }
    }

@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    """Serve dashboard HTML"""
    template_path = Path(__file__).parent / "templates" / "dashboard.html"
    
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    else:
        return HTMLResponse(content="<h1>Dashboard template not found</h1>")

@app.get("/api/data")
async def get_data():
    """Get current dashboard data"""
    return dashboard_data

@app.get("/api/nodes")
async def get_nodes():
    """Get all registered nodes"""
    return {
        "nodes": dashboard_data["nodes"],
        "count": len(dashboard_data["nodes"])
    }

@app.post("/api/nodes/register")
async def register_node(node: NodeRegistration):
    """Register a new node dynamically"""
    if node.node_id in dashboard_data["nodes"]:
        raise HTTPException(status_code=400, detail="Node already registered")
    
    dashboard_data["nodes"][node.node_id] = init_node_data(node.node_id, node.node_type)
    if node.description:
        dashboard_data["nodes"][node.node_id]["description"] = node.description
    
    print(f"[Dashboard] ✅ Registered new node: {node.node_id} (type: {node.node_type})")
    
    # Broadcast node registration
    await broadcast_update("/system/node_registered", {
        "node_id": node.node_id,
        "node_type": node.node_type
    })
    
    return {"status": "success", "node": dashboard_data["nodes"][node.node_id]}

@app.delete("/api/nodes/{node_id}")
async def unregister_node(node_id: str):
    """Unregister a node"""
    if node_id not in dashboard_data["nodes"]:
        raise HTTPException(status_code=404, detail="Node not found")
    
    del dashboard_data["nodes"][node_id]
    print(f"[Dashboard] ❌ Unregistered node: {node_id}")
    
    # Broadcast node removal
    await broadcast_update("/system/node_unregistered", {"node_id": node_id})
    
    return {"status": "success", "message": f"Node {node_id} unregistered"}

@app.get("/api/metrics")
async def get_metrics():
    """Get system-wide metrics"""
    return {
        "system_metrics": dashboard_data["system_metrics"],
        "attack_resilience": dashboard_data["attack_resilience"],
        "node_count": len(dashboard_data["nodes"]),
        "active_nodes": sum(1 for node in dashboard_data["nodes"].values() 
                           if node.get("status") not in ["unknown", "offline"]),
        "timestamp": datetime.now().isoformat()
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for realtime updates"""
    await websocket.accept()
    active_connections.append(websocket)
    print(f"[Dashboard] 🔌 WebSocket connected. Total: {len(active_connections)}")
    
    # Send initial data
    try:
        await websocket.send_json({
            "type": "initial_data",
            "dashboard_data": dashboard_data,
            "timestamp": datetime.now().isoformat()
        })
    except:
        pass
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            
            # Echo back (heartbeat)
            if data == "ping":
                await websocket.send_text("pong")
            
            # Handle commands
            elif data.startswith("cmd:"):
                command = data[4:]
                if command == "get_metrics":
                    await websocket.send_json({
                        "type": "metrics",
                        "data": await get_metrics()
                    })
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        print(f"[Dashboard] 🔌 WebSocket disconnected. Total: {len(active_connections)}")

if __name__ == "__main__":
    print("=" * 70)
    print("IoT Fault-Tolerant Dashboard Server (IMPROVED)")
    print("=" * 70)
    print("Dashboard URL: http://localhost:8000/dashboard")
    print("API URL: http://localhost:8000/api/data")
    print("Metrics URL: http://localhost:8000/api/metrics")
    print("=" * 70)
    print("\n📊 Improvements:")
    print("  - Dynamic node registration/removal")
    print("  - Real-time metrics aggregation")
    print("  - Communication flow tracking")
    print("  - Attack resilience monitoring")
    print("  - Auto-discovery of new nodes\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
