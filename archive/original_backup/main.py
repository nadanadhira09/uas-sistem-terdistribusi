"""
Web Dashboard - FastAPI + WebSocket untuk monitoring realtime
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import paho.mqtt.client as mqtt
import json
import asyncio
from datetime import datetime
from typing import List, Dict
import uvicorn
from pathlib import Path

app = FastAPI(title="IoT Fault-Tolerant Dashboard")

# Mount static files
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# WebSocket connections
active_connections: List[WebSocket] = []

# Data storage
dashboard_data = {
    "node_a": {
        "status": "unknown",
        "broker": "unknown",
        "failover_count": 0,
        "reconnect_count": 0,
        "last_update": None,
        "data_count": 0,
        "latest_data": {}
    },
    "node_b": {
        "status": "unknown",
        "mode": "unknown",
        "offline_decisions": 0,
        "retry_count": 0,
        "last_update": None,
        "data_count": 0,
        "latest_data": {}
    },
    "node_c": {
        "status": "idle",
        "total_messages": 0,
        "messages_per_second": 0,
        "topics_created": 0,
        "last_update": None
    },
    "statistics": {
        "total_messages_received": 0,
        "uptime_start": datetime.now().isoformat()
    }
}

# MQTT Client
mqtt_client = None

def on_connect(client, userdata, flags, rc):
    """MQTT on connect callback"""
    if rc == 0:
        print("[Dashboard] Connected to MQTT broker")
        # Subscribe to all relevant topics
        client.subscribe("/nodeA/data")
        client.subscribe("/nodeA/status")
        client.subscribe("/nodeB/data")
        client.subscribe("/nodeB/status")
        client.subscribe("/nodeC/attack_status")
        client.subscribe("/attack/#")
        client.subscribe("/spam/#")
        print("[Dashboard] Subscribed to all topics")
    else:
        print(f"[Dashboard] Connection failed with code {rc}")

def on_message(client, userdata, msg):
    """MQTT on message callback"""
    try:
        payload = json.loads(msg.payload.decode())
        topic = msg.topic
        
        # Update dashboard data
        update_dashboard_data(topic, payload)
        
        # Broadcast to all websocket connections
        asyncio.run(broadcast_update(topic, payload))
        
    except Exception as e:
        print(f"[Dashboard] Error processing message: {e}")

def update_dashboard_data(topic: str, payload: dict):
    """Update internal dashboard data"""
    now = datetime.now().isoformat()
    
    dashboard_data["statistics"]["total_messages_received"] += 1
    
    if topic == "/nodeA/data":
        dashboard_data["node_a"]["latest_data"] = payload
        dashboard_data["node_a"]["data_count"] += 1
        dashboard_data["node_a"]["last_update"] = now
        if "broker" in payload:
            dashboard_data["node_a"]["broker"] = payload["broker"]
    
    elif topic == "/nodeA/status":
        dashboard_data["node_a"]["status"] = payload.get("event", "unknown")
        dashboard_data["node_a"]["broker"] = payload.get("broker", "unknown")
        dashboard_data["node_a"]["failover_count"] = payload.get("failover_count", 0)
        dashboard_data["node_a"]["reconnect_count"] = payload.get("reconnect_count", 0)
        dashboard_data["node_a"]["last_update"] = now
    
    elif topic == "/nodeB/data":
        dashboard_data["node_b"]["latest_data"] = payload
        dashboard_data["node_b"]["data_count"] += 1
        dashboard_data["node_b"]["last_update"] = now
        if "mode" in payload:
            dashboard_data["node_b"]["mode"] = payload["mode"]
    
    elif topic == "/nodeB/status":
        dashboard_data["node_b"]["status"] = payload.get("event", "unknown")
        dashboard_data["node_b"]["mode"] = payload.get("mode", "unknown")
        dashboard_data["node_b"]["offline_decisions"] = payload.get("offline_decisions", 0)
        dashboard_data["node_b"]["retry_count"] = payload.get("retry_count", 0)
        dashboard_data["node_b"]["last_update"] = now
    
    elif topic == "/nodeC/attack_status":
        dashboard_data["node_c"]["status"] = payload.get("status", "unknown")
        dashboard_data["node_c"]["total_messages"] = payload.get("total_messages", 0)
        dashboard_data["node_c"]["messages_per_second"] = payload.get("messages_per_second", 0)
        dashboard_data["node_c"]["topics_created"] = payload.get("topics_created", 0)
        dashboard_data["node_c"]["last_update"] = now
    
    elif topic.startswith("/attack/") or topic.startswith("/spam/"):
        # Count attack messages
        dashboard_data["node_c"]["total_messages"] = dashboard_data["node_c"].get("total_messages", 0) + 1

async def broadcast_update(topic: str, payload: dict):
    """Broadcast update to all connected websockets"""
    message = {
        "type": "mqtt_update",
        "topic": topic,
        "payload": payload,
        "dashboard_data": dashboard_data
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
    
    mqtt_client = mqtt.Client(client_id=f"dashboard_{int(datetime.now().timestamp())}")
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    
    try:
        mqtt_client.connect("localhost", 1883, keepalive=60)
        mqtt_client.loop_start()
        print("[Dashboard] MQTT client started")
    except Exception as e:
        print(f"[Dashboard] Failed to connect to MQTT broker: {e}")

@app.on_event("startup")
async def startup_event():
    """Startup event"""
    print("[Dashboard] Starting IoT Dashboard...")
    start_mqtt_client()

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event"""
    print("[Dashboard] Shutting down...")
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()

@app.get("/")
async def root():
    """Root endpoint - redirect to dashboard"""
    return {"message": "IoT Fault-Tolerant Dashboard API", "dashboard": "/dashboard"}

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

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for realtime updates"""
    await websocket.accept()
    active_connections.append(websocket)
    print(f"[Dashboard] WebSocket connected. Total connections: {len(active_connections)}")
    
    # Send initial data
    try:
        await websocket.send_json({
            "type": "initial_data",
            "dashboard_data": dashboard_data
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
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        print(f"[Dashboard] WebSocket disconnected. Total connections: {len(active_connections)}")

if __name__ == "__main__":
    print("=" * 60)
    print("IoT Fault-Tolerant Dashboard Server")
    print("=" * 60)
    print("Dashboard URL: http://localhost:8000/dashboard")
    print("API URL: http://localhost:8000/api/data")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
