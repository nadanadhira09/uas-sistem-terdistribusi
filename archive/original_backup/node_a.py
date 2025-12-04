"""
Node A - IoT Device dengan Failover dan Self-Healing
Fitur:
- Failover otomatis (Broker A -> Broker B)
- Self-Healing (restart koneksi saat stuck)
- Multi-threading (sensor data + health check)
"""

import paho.mqtt.client as mqtt
import json
import time
import random
import threading
from datetime import datetime
from typing import Optional

class NodeA:
    def __init__(self):
        self.broker_primary = "localhost"
        self.broker_backup = "localhost"
        self.port_primary = 1883
        self.port_backup = 1884
        self.client: Optional[mqtt.Client] = None
        self.current_broker = "A"
        self.is_connected = False
        self.failover_count = 0
        self.reconnect_count = 0
        self.running = True
        self.lock = threading.Lock()
        self.last_health_check = time.time()
        
        # Topics
        self.topic_data = "/nodeA/data"
        self.topic_status = "/nodeA/status"
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback saat koneksi berhasil"""
        if rc == 0:
            print(f"[Node A] Connected to Broker {self.current_broker} (rc={rc})")
            with self.lock:
                self.is_connected = True
                self.last_health_check = time.time()
            
            # Publish status connection
            self.publish_status("connected", f"Connected to Broker {self.current_broker}")
        else:
            print(f"[Node A] Connection failed with code {rc}")
            with self.lock:
                self.is_connected = False
    
    def on_disconnect(self, client, userdata, rc):
        """Callback saat disconnect"""
        print(f"[Node A] Disconnected from Broker {self.current_broker} (rc={rc})")
        with self.lock:
            self.is_connected = False
        
        if rc != 0:
            print(f"[Node A] Unexpected disconnect! Attempting self-healing...")
            self.self_healing()
    
    def on_publish(self, client, userdata, mid):
        """Callback saat publish berhasil"""
        with self.lock:
            self.last_health_check = time.time()
    
    def connect_to_broker(self, broker: str, port: int) -> bool:
        """Koneksi ke broker"""
        try:
            self.client = mqtt.Client(client_id=f"node_a_{int(time.time())}")
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_publish = self.on_publish
            
            print(f"[Node A] Connecting to {broker}:{port}...")
            self.client.connect(broker, port, keepalive=60)
            self.client.loop_start()
            
            # Wait for connection
            timeout = 5
            start_time = time.time()
            while not self.is_connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            return self.is_connected
        except Exception as e:
            print(f"[Node A] Connection error: {e}")
            return False
    
    def failover(self):
        """Failover ke broker backup"""
        print(f"[Node A] Initiating FAILOVER from Broker {self.current_broker}...")
        
        with self.lock:
            self.failover_count += 1
        
        # Disconnect dari broker sekarang
        if self.client:
            try:
                self.client.loop_stop()
                self.client.disconnect()
            except:
                pass
        
        # Switch broker
        if self.current_broker == "A":
            self.current_broker = "B"
            success = self.connect_to_broker(self.broker_backup, self.port_backup)
        else:
            self.current_broker = "A"
            success = self.connect_to_broker(self.broker_primary, self.port_primary)
        
        if success:
            print(f"[Node A] FAILOVER SUCCESS! Now using Broker {self.current_broker}")
            self.publish_status("failover", f"Failover to Broker {self.current_broker} (count: {self.failover_count})")
        else:
            print(f"[Node A] FAILOVER FAILED! Broker {self.current_broker} unavailable")
            # Try other broker
            time.sleep(2)
            self.failover()
    
    def self_healing(self):
        """Self-healing: restart koneksi saat stuck"""
        print(f"[Node A] Starting SELF-HEALING process...")
        
        with self.lock:
            self.reconnect_count += 1
        
        # Tunggu sebentar
        time.sleep(2)
        
        # Try reconnect ke broker saat ini
        if self.current_broker == "A":
            success = self.connect_to_broker(self.broker_primary, self.port_primary)
        else:
            success = self.connect_to_broker(self.broker_backup, self.port_backup)
        
        if not success:
            print(f"[Node A] Self-healing failed, attempting failover...")
            self.failover()
        else:
            print(f"[Node A] SELF-HEALING SUCCESS! (count: {self.reconnect_count})")
            self.publish_status("self_healing", f"Self-healing completed (count: {self.reconnect_count})")
    
    def publish_status(self, event_type: str, message: str):
        """Publish status ke broker"""
        if self.client and self.is_connected:
            payload = {
                "node": "A",
                "event": event_type,
                "message": message,
                "broker": self.current_broker,
                "failover_count": self.failover_count,
                "reconnect_count": self.reconnect_count,
                "timestamp": datetime.now().isoformat()
            }
            try:
                self.client.publish(self.topic_status, json.dumps(payload), qos=1)
            except Exception as e:
                print(f"[Node A] Publish status error: {e}")
    
    def publish_sensor_data(self):
        """Publish data sensor"""
        if self.client and self.is_connected:
            payload = {
                "node": "A",
                "temperature": round(random.uniform(20.0, 35.0), 2),
                "humidity": round(random.uniform(40.0, 80.0), 2),
                "pressure": round(random.uniform(980.0, 1020.0), 2),
                "broker": self.current_broker,
                "timestamp": datetime.now().isoformat()
            }
            try:
                result = self.client.publish(self.topic_data, json.dumps(payload), qos=1)
                if result.rc != mqtt.MQTT_ERR_SUCCESS:
                    print(f"[Node A] Publish failed with rc={result.rc}")
                    return False
                return True
            except Exception as e:
                print(f"[Node A] Publish data error: {e}")
                return False
        return False
    
    def sensor_thread(self):
        """Thread untuk simulasi sensor dan publish data"""
        print("[Node A] Sensor thread started")
        while self.running:
            if self.is_connected:
                success = self.publish_sensor_data()
                if not success:
                    print("[Node A] Sensor data publish failed")
            time.sleep(2)  # Publish setiap 2 detik
    
    def health_check_thread(self):
        """Thread untuk monitoring kesehatan koneksi"""
        print("[Node A] Health check thread started")
        while self.running:
            time.sleep(5)  # Check setiap 5 detik
            
            if not self.is_connected:
                print("[Node A] Health check: NOT CONNECTED - triggering failover")
                self.failover()
            else:
                # Check timeout (jika tidak ada aktivitas dalam 15 detik)
                with self.lock:
                    idle_time = time.time() - self.last_health_check
                
                if idle_time > 15:
                    print(f"[Node A] Health check: TIMEOUT detected ({idle_time:.1f}s) - triggering self-healing")
                    self.self_healing()
                else:
                    print(f"[Node A] Health check: OK (broker={self.current_broker}, idle={idle_time:.1f}s)")
    
    def start(self):
        """Start Node A"""
        print("=" * 60)
        print("Node A - IoT Device with Failover & Self-Healing")
        print("=" * 60)
        
        # Connect ke broker primary
        success = self.connect_to_broker(self.broker_primary, self.port_primary)
        
        if not success:
            print("[Node A] Primary broker unavailable, trying backup...")
            self.failover()
        
        # Start threads
        sensor_t = threading.Thread(target=self.sensor_thread, daemon=True)
        health_t = threading.Thread(target=self.health_check_thread, daemon=True)
        
        sensor_t.start()
        health_t.start()
        
        print("[Node A] All threads started. Press Ctrl+C to stop.")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[Node A] Stopping...")
            self.running = False
            if self.client:
                self.publish_status("shutdown", "Node A shutting down")
                self.client.loop_stop()
                self.client.disconnect()
            print("[Node A] Stopped.")

if __name__ == "__main__":
    node = NodeA()
    node.start()
