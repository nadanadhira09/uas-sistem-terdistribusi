"""
Node B - IoT Device dengan Edge Processing dan Offline Mode
Fitur:
- Edge processing (pemrosesan lokal)
- Offline mode (tetap bisa ambil keputusan tanpa broker)
- Fallback retry (tidak ada failover)
"""

import paho.mqtt.client as mqtt
import json
import time
import random
import threading
from datetime import datetime
from typing import Optional
from collections import deque

class NodeB:
    def __init__(self):
        self.broker = "localhost"
        self.port = 1883
        self.client: Optional[mqtt.Client] = None
        self.is_connected = False
        self.is_online_mode = True
        self.running = True
        self.lock = threading.Lock()
        self.retry_count = 0
        self.max_retries = 5
        self.offline_decisions = 0
        
        # Edge processing - data buffer
        self.sensor_buffer = deque(maxlen=100)
        self.processed_data = {}
        
        # Topics
        self.topic_data = "/nodeB/data"
        self.topic_status = "/nodeB/status"
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback saat koneksi berhasil"""
        if rc == 0:
            print(f"[Node B] Connected to Broker (rc={rc})")
            with self.lock:
                self.is_connected = True
                self.is_online_mode = True
                self.retry_count = 0
        else:
            print(f"[Node B] Connection failed with code {rc}")
            with self.lock:
                self.is_connected = False
    
    def on_disconnect(self, client, userdata, rc):
        """Callback saat disconnect"""
        print(f"[Node B] Disconnected from Broker (rc={rc})")
        with self.lock:
            self.is_connected = False
            self.is_online_mode = False
        
        if rc != 0:
            print(f"[Node B] Unexpected disconnect! Entering OFFLINE MODE...")
            self.retry_connection()
    
    def on_publish(self, client, userdata, mid):
        """Callback saat publish berhasil"""
        pass
    
    def connect_to_broker(self) -> bool:
        """Koneksi ke broker"""
        try:
            self.client = mqtt.Client(client_id=f"node_b_{int(time.time())}")
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_publish = self.on_publish
            
            print(f"[Node B] Connecting to {self.broker}:{self.port}...")
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            
            # Wait for connection
            timeout = 5
            start_time = time.time()
            while not self.is_connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            return self.is_connected
        except Exception as e:
            print(f"[Node B] Connection error: {e}")
            return False
    
    def retry_connection(self):
        """Retry koneksi dengan fallback"""
        with self.lock:
            self.retry_count += 1
        
        print(f"[Node B] Retry connection attempt {self.retry_count}/{self.max_retries}...")
        
        # Exponential backoff
        wait_time = min(2 ** self.retry_count, 30)
        time.sleep(wait_time)
        
        success = self.connect_to_broker()
        
        if success:
            print(f"[Node B] Reconnection SUCCESS after {self.retry_count} attempts!")
            with self.lock:
                self.is_online_mode = True
                self.retry_count = 0
            self.publish_status("reconnected", f"Back online after {self.retry_count} retries")
        else:
            if self.retry_count < self.max_retries:
                print(f"[Node B] Retry failed, attempting again...")
                self.retry_connection()
            else:
                print(f"[Node B] Max retries reached. Staying in OFFLINE MODE.")
                with self.lock:
                    self.retry_count = 0
                    self.is_online_mode = False
    
    def edge_processing(self, sensor_data: dict) -> dict:
        """
        Edge Processing: Proses data secara lokal
        - Hitung statistik (avg, min, max)
        - Deteksi anomali
        - Ambil keputusan lokal
        """
        self.sensor_buffer.append(sensor_data)
        
        # Hitung statistik dari buffer
        if len(self.sensor_buffer) >= 5:
            temps = [d['temperature'] for d in self.sensor_buffer]
            humids = [d['humidity'] for d in self.sensor_buffer]
            
            avg_temp = sum(temps) / len(temps)
            avg_humid = sum(humids) / len(humids)
            
            # Deteksi anomali (suhu terlalu tinggi)
            anomaly = sensor_data['temperature'] > 32.0
            
            # Keputusan lokal
            if anomaly:
                decision = "ALERT: High temperature detected!"
                action = "cooling_on"
            elif avg_temp > 28.0:
                decision = "WARNING: Average temperature elevated"
                action = "monitor"
            else:
                decision = "NORMAL: All parameters within range"
                action = "none"
            
            processed = {
                "raw_data": sensor_data,
                "statistics": {
                    "avg_temperature": round(avg_temp, 2),
                    "avg_humidity": round(avg_humid, 2),
                    "samples": len(self.sensor_buffer)
                },
                "anomaly_detected": anomaly,
                "decision": decision,
                "action": action,
                "processed_at": datetime.now().isoformat()
            }
            
            self.processed_data = processed
            return processed
        else:
            return {
                "raw_data": sensor_data,
                "message": "Collecting data for edge processing...",
                "samples": len(self.sensor_buffer)
            }
    
    def publish_status(self, event_type: str, message: str):
        """Publish status ke broker"""
        if self.client and self.is_connected:
            payload = {
                "node": "B",
                "event": event_type,
                "message": message,
                "mode": "online" if self.is_online_mode else "offline",
                "retry_count": self.retry_count,
                "offline_decisions": self.offline_decisions,
                "timestamp": datetime.now().isoformat()
            }
            try:
                self.client.publish(self.topic_status, json.dumps(payload), qos=1)
            except Exception as e:
                print(f"[Node B] Publish status error: {e}")
    
    def publish_data(self, data: dict):
        """Publish data ke broker (jika online)"""
        if self.client and self.is_connected:
            try:
                self.client.publish(self.topic_data, json.dumps(data), qos=1)
                return True
            except Exception as e:
                print(f"[Node B] Publish data error: {e}")
                return False
        return False
    
    def sensor_and_processing_thread(self):
        """Thread untuk sensor + edge processing"""
        print("[Node B] Sensor and processing thread started")
        
        while self.running:
            # Simulate sensor reading
            sensor_data = {
                "node": "B",
                "temperature": round(random.uniform(20.0, 35.0), 2),
                "humidity": round(random.uniform(40.0, 80.0), 2),
                "light": round(random.uniform(100.0, 1000.0), 2),
                "timestamp": datetime.now().isoformat()
            }
            
            # Edge processing (selalu jalan, online atau offline)
            processed = self.edge_processing(sensor_data)
            
            # Tambahkan info mode
            processed["mode"] = "online" if self.is_online_mode else "offline"
            processed["node"] = "B"
            
            if self.is_online_mode and self.is_connected:
                # Online mode: publish ke broker
                success = self.publish_data(processed)
                if success:
                    print(f"[Node B] [ONLINE] Published data - Decision: {processed.get('decision', 'N/A')}")
                else:
                    print(f"[Node B] [ONLINE] Failed to publish, switching to offline mode")
                    with self.lock:
                        self.is_online_mode = False
            else:
                # Offline mode: keputusan lokal saja
                with self.lock:
                    self.offline_decisions += 1
                
                print(f"[Node B] [OFFLINE] Local decision #{self.offline_decisions}: {processed.get('decision', 'N/A')}")
                
                # Coba reconnect setiap 10 keputusan offline
                if self.offline_decisions % 10 == 0:
                    print(f"[Node B] Attempting reconnection after {self.offline_decisions} offline decisions...")
                    threading.Thread(target=self.retry_connection, daemon=True).start()
            
            time.sleep(3)  # Process setiap 3 detik
    
    def status_monitor_thread(self):
        """Thread untuk monitoring status"""
        print("[Node B] Status monitor thread started")
        
        while self.running:
            time.sleep(10)
            
            mode = "ONLINE" if self.is_online_mode else "OFFLINE"
            status = "Connected" if self.is_connected else "Disconnected"
            
            print(f"[Node B] Status: {mode} | {status} | Offline Decisions: {self.offline_decisions}")
            
            if self.is_connected:
                self.publish_status("heartbeat", f"Mode: {mode}, Status: {status}")
    
    def start(self):
        """Start Node B"""
        print("=" * 60)
        print("Node B - IoT Device with Edge Processing & Offline Mode")
        print("=" * 60)
        
        # Connect ke broker
        success = self.connect_to_broker()
        
        if not success:
            print("[Node B] Broker unavailable, starting in OFFLINE MODE...")
            with self.lock:
                self.is_online_mode = False
        
        # Start threads
        processing_t = threading.Thread(target=self.sensor_and_processing_thread, daemon=True)
        monitor_t = threading.Thread(target=self.status_monitor_thread, daemon=True)
        
        processing_t.start()
        monitor_t.start()
        
        print("[Node B] All threads started. Press Ctrl+C to stop.")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[Node B] Stopping...")
            self.running = False
            if self.client and self.is_connected:
                self.publish_status("shutdown", "Node B shutting down")
                self.client.loop_stop()
                self.client.disconnect()
            print("[Node B] Stopped.")

if __name__ == "__main__":
    node = NodeB()
    node.start()
