"""
Node B - Backup Sensor dengan Active-Passive Failover
Fitur:
- Detect Node A crash dan mengambil alih sebagai sensor backup
- Buffer data saat mode backup aktif
- Sync data ke Node A setelah recovery
- Real-time monitoring Node A status
"""

import paho.mqtt.client as mqtt
import json
import time
import random
import threading
from datetime import datetime
from typing import Optional
from collections import deque

class NodeBFailover:
    def __init__(self):
        self.broker = "localhost"
        self.port = 1883
        self.client: Optional[mqtt.Client] = None
        self.is_connected = False
        self.running = True
        self.lock = threading.Lock()
        
        # Backup mode untuk failover
        self.is_backup_mode = False  # True saat Node A down
        self.node_a_status = "active"  # 'active', 'crashed', 'recovering'
        self.backup_data_buffer = deque(maxlen=500)  # Simpan data saat backup mode
        self.last_node_a_heartbeat = time.time()
        self.node_a_timeout = 10  # detik
        
        # Edge processing
        self.sensor_buffer = deque(maxlen=100)
        self.messages_sent = 0
        
        # Topics
        self.topic_data = "/nodeB/data"
        self.topic_status = "/nodeB/status"
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback saat koneksi berhasil"""
        if rc == 0:
            print(f"[Node B] ✅ Connected to broker (rc={rc})")
            with self.lock:
                self.is_connected = True
            
            # Subscribe to system alerts dan Node A status
            self.client.subscribe("/system/alert", qos=1)
            self.client.subscribe("/nodeA/status", qos=1)
            self.client.subscribe("/nodeB/command", qos=1)
            print("[Node B] 🔔 Subscribed to system alerts and Node A status")
            
            self.publish_status("connected", "Node B ready as backup sensor")
        else:
            print(f"[Node B] ❌ Connection failed with code {rc}")
            with self.lock:
                self.is_connected = False
    
    def on_disconnect(self, client, userdata, rc):
        """Callback saat disconnect"""
        print(f"[Node B] ⚠️ Disconnected from broker (rc={rc})")
        with self.lock:
            self.is_connected = False
    
    def on_message(self, client, userdata, msg):
        """Callback when message received"""
        try:
            payload = json.loads(msg.payload.decode())
            
            # Handle system alerts
            if msg.topic == "/system/alert":
                event = payload.get("event")
                
                if event == "CRASHED":
                    print("\n" + "="*70)
                    print("⚠️  ALERT: NODE A HAS CRASHED!")
                    print("="*70)
                    print("[Node B] 🔄 ACTIVATING BACKUP MODE...")
                    with self.lock:
                        self.is_backup_mode = True
                        self.node_a_status = "crashed"
                    self.publish_status("backup_activated", "Node B taking over as primary sensor")
                    print("[Node B] ✅ BACKUP MODE ACTIVE - Acting as primary sensor\n")
                
                elif event == "RECOVERY_COMPLETE":
                    print("\n" + "="*70)
                    print("✅ NODE A HAS RECOVERED!")
                    print("="*70)
                    print(f"[Node B] 📤 Syncing {len(self.backup_data_buffer)} buffered messages to Node A...")
                    self.sync_data_to_node_a()
                    with self.lock:
                        self.is_backup_mode = False
                        self.node_a_status = "active"
                    self.publish_status("backup_deactivated", "Node A recovered, returning to edge computing mode")
                    print("[Node B] 🔙 Returning to EDGE COMPUTING MODE\n")
            
            # Handle Node A status updates
            elif msg.topic == "/nodeA/status":
                with self.lock:
                    self.last_node_a_heartbeat = time.time()
                    if payload.get("is_primary_active"):
                        self.node_a_status = "active"
            
            # Handle commands
            elif msg.topic == "/nodeB/command":
                command = payload.get("command")
                if command == "sync_data":
                    self.sync_data_to_node_a()
        
        except Exception as e:
            print(f"[Node B] ❌ Error processing message: {e}")
    
    def sync_data_to_node_a(self):
        """Sync buffered data to Node A after recovery"""
        if not self.backup_data_buffer:
            print("[Node B] ℹ️ No data to sync.")
            return
        
        print(f"[Node B] 📤 Syncing {len(self.backup_data_buffer)} messages to Node A...")
        
        sync_payload = {
            "node": "B",
            "event": "data_sync",
            "message": f"Transferring {len(self.backup_data_buffer)} buffered messages",
            "data_count": len(self.backup_data_buffer),
            "buffered_data": list(self.backup_data_buffer),
            "timestamp": datetime.now().isoformat()
        }
        
        if self.client and self.is_connected:
            try:
                self.client.publish("/nodeA/sync", json.dumps(sync_payload), qos=1)
                print(f"[Node B] ✅ Data sync completed! {len(self.backup_data_buffer)} messages transferred.")
                
                # Clear buffer after sync
                self.backup_data_buffer.clear()
            except Exception as e:
                print(f"[Node B] ❌ Data sync failed: {e}")
    
    def connect_to_broker(self) -> bool:
        """Koneksi ke broker"""
        try:
            self.client = mqtt.Client(
                client_id=f"node_b_{int(time.time())}",
                callback_api_version=mqtt.CallbackAPIVersion.VERSION1
            )
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_message = self.on_message
            
            print(f"[Node B] 🔌 Connecting to {self.broker}:{self.port}...")
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            
            # Wait for connection
            timeout = 5
            start_time = time.time()
            while not self.is_connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            return self.is_connected
        except Exception as e:
            print(f"[Node B] ❌ Connection error: {e}")
            return False
    
    def edge_processing(self, sensor_data: dict) -> dict:
        """Edge Processing sederhana"""
        self.sensor_buffer.append(sensor_data)
        
        if len(self.sensor_buffer) >= 5:
            temps = [d['temperature'] for d in self.sensor_buffer]
            humids = [d['humidity'] for d in self.sensor_buffer]
            
            avg_temp = sum(temps) / len(temps)
            avg_humid = sum(humids) / len(humids)
            
            anomaly = sensor_data['temperature'] > 32.0
            
            if anomaly:
                decision = "ALERT: High temperature!"
                action = "cooling_on"
            else:
                decision = "NORMAL"
                action = "none"
            
            return {
                "raw_data": sensor_data,
                "statistics": {
                    "avg_temperature": round(avg_temp, 2),
                    "avg_humidity": round(avg_humid, 2),
                },
                "anomaly_detected": anomaly,
                "decision": decision,
                "action": action,
                "processed_at": datetime.now().isoformat()
            }
        else:
            return {
                "raw_data": sensor_data,
                "message": "Collecting data...",
                "samples": len(self.sensor_buffer)
            }
    
    def publish_status(self, event_type: str, message: str):
        """Publish status"""
        if self.client and self.is_connected:
            payload = {
                "node": "B",
                "type": "edge",
                "event": event_type,
                "message": message,
                "is_backup_mode": self.is_backup_mode,
                "node_a_status": self.node_a_status,
                "buffer_size": len(self.backup_data_buffer),
                "timestamp": datetime.now().isoformat()
            }
            try:
                self.client.publish(self.topic_status, json.dumps(payload), qos=1)
            except Exception as e:
                print(f"[Node B] ❌ Publish status error: {e}")
    
    def publish_sensor_data(self):
        """Publish sensor data (hanya saat backup mode)"""
        if self.client and self.is_connected and self.is_backup_mode:
            sensor_data = {
                "node": "B_BACKUP",
                "temperature": round(random.uniform(20.0, 35.0), 2),
                "humidity": round(random.uniform(40.0, 80.0), 2),
                "pressure": round(random.uniform(980.0, 1020.0), 2),
                "mode": "BACKUP",
                "timestamp": datetime.now().isoformat()
            }
            
            # Store in buffer untuk sync nanti
            self.backup_data_buffer.append(sensor_data.copy())
            
            try:
                result = self.client.publish("/nodeA/data", json.dumps(sensor_data), qos=1)
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    self.messages_sent += 1
                    return True
            except Exception as e:
                print(f"[Node B] ❌ Publish error: {e}")
        return False
    
    def sensor_thread(self):
        """Thread untuk sensor (backup mode)"""
        print("[Node B] 📡 Backup sensor thread started")
        while self.running:
            if self.is_backup_mode:
                success = self.publish_sensor_data()
                if success:
                    print(f"[Node B] [BACKUP MODE] 📤 Sensor data published (buffered: {len(self.backup_data_buffer)})")
            else:
                # Normal mode: edge computing
                sensor_data = {
                    "temperature": round(random.uniform(20.0, 35.0), 2),
                    "humidity": round(random.uniform(40.0, 80.0), 2),
                }
                processed = self.edge_processing(sensor_data)
                
                if self.client and self.is_connected:
                    processed["node"] = "B"
                    processed["type"] = "edge"
                    try:
                        self.client.publish(self.topic_data, json.dumps(processed), qos=1)
                        print(f"[Node B] [EDGE MODE] 🔧 Processed: {processed.get('decision', 'N/A')}")
                    except:
                        pass
            
            time.sleep(2)
    
    def monitor_thread(self):
        """Monitor Node A status"""
        print("[Node B] 👁️ Node A monitor started")
        while self.running:
            time.sleep(5)
            
            mode = "BACKUP" if self.is_backup_mode else "EDGE"
            print(f"[Node B] 📊 Mode: {mode} | Node A: {self.node_a_status} | Buffer: {len(self.backup_data_buffer)}")
            
            # Publish periodic status update (especially important for buffer size)
            if self.is_connected:
                self.publish_status("heartbeat", f"Mode: {mode}, Buffer: {len(self.backup_data_buffer)}")
            
            # Check Node A heartbeat timeout
            if not self.is_backup_mode:
                time_since_heartbeat = time.time() - self.last_node_a_heartbeat
                if time_since_heartbeat > self.node_a_timeout:
                    print(f"[Node B] ⚠️ Node A heartbeat timeout ({time_since_heartbeat:.1f}s)")
    
    def start(self):
        """Start Node B"""
        print("=" * 70)
        print("Node B - Backup Sensor with Active-Passive Failover")
        print("=" * 70)
        
        success = self.connect_to_broker()
        
        if not success:
            print("[Node B] ⚠️ Broker unavailable!")
            return
        
        # Start threads
        sensor_t = threading.Thread(target=self.sensor_thread, daemon=True)
        monitor_t = threading.Thread(target=self.monitor_thread, daemon=True)
        
        sensor_t.start()
        monitor_t.start()
        
        print("[Node B] ✅ All threads started. Press Ctrl+C to stop.")
        print("\n⚡ Features:")
        print("  - Auto-detect Node A crash")
        print("  - Activate backup mode automatically")
        print("  - Buffer data during backup period")
        print("  - Auto-sync to Node A after recovery\n")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[Node B] 🛑 Stopping...")
            self.running = False
            if self.client:
                self.publish_status("shutdown", "Node B shutting down")
                self.client.loop_stop()
                self.client.disconnect()
            print("[Node B] ✅ Stopped.")

if __name__ == "__main__":
    node = NodeBFailover()
    node.start()
