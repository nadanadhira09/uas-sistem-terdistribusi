"""
Node A - IoT Device dengan Failover dan Self-Healing (IMPROVED VERSION)
Fitur Baru:
- Recovery time tracking (mengukur kecepatan pulih)
- Message latency monitoring
- Success/failure rate tracking
- Detailed metrics untuk analisis performa
"""

import paho.mqtt.client as mqtt
import json
import time
import random
import threading
from datetime import datetime
from typing import Optional
from collections import deque

class NodeAImproved:
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
        
        # NEW: Crash simulation for active-passive failover testing
        self.is_primary_active = True
        self.crash_simulation_enabled = False
        self.crash_recovery_time = 15  # seconds to stay "crashed"
        
        # NEW: Recovery time tracking
        self.recovery_times = deque(maxlen=50)
        self.failure_start_time = None
        self.avg_recovery_time = 0
        self.fastest_recovery = None
        self.slowest_recovery = None
        
        # NEW: Message tracking
        self.messages_sent = 0
        self.messages_failed = 0
        self.message_success_rate = 100.0
        self.message_latencies = deque(maxlen=100)
        self.avg_latency = 0
        
        # NEW: System health metrics
        self.uptime_start = time.time()
        self.total_downtime = 0
        self.downtime_start = None
        
        # Topics
        self.topic_data = "/nodeA/data"
        self.topic_status = "/nodeA/status"
        self.topic_metrics = "/nodeA/metrics"
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback saat koneksi berhasil"""
        if rc == 0:
            print(f"[Node A] ✅ Connected to Broker {self.current_broker} (rc={rc})")
            with self.lock:
                self.is_connected = True
                self.last_health_check = time.time()
                
                # Track recovery time
                if self.failure_start_time:
                    recovery_time = time.time() - self.failure_start_time
                    self.recovery_times.append(recovery_time)
                    
                    # Update recovery statistics
                    self.avg_recovery_time = sum(self.recovery_times) / len(self.recovery_times)
                    if self.fastest_recovery is None or recovery_time < self.fastest_recovery:
                        self.fastest_recovery = recovery_time
                    if self.slowest_recovery is None or recovery_time > self.slowest_recovery:
                        self.slowest_recovery = recovery_time
                    
                    print(f"[Node A] 🔄 Recovery completed in {recovery_time:.2f}s "
                          f"(avg: {self.avg_recovery_time:.2f}s)")
                    
                    self.failure_start_time = None
                
                # Stop downtime tracking
                if self.downtime_start:
                    self.total_downtime += time.time() - self.downtime_start
                    self.downtime_start = None
            
            # Publish status connection
            self.publish_status("connected", f"Connected to Broker {self.current_broker}")
            self.publish_metrics()
        else:
            print(f"[Node A] ❌ Connection failed with code {rc}")
            with self.lock:
                self.is_connected = False
    
    def on_disconnect(self, client, userdata, rc):
        """Callback saat disconnect"""
        print(f"[Node A] ⚠️ Disconnected from Broker {self.current_broker} (rc={rc})")
        with self.lock:
            self.is_connected = False
            if not self.failure_start_time:
                self.failure_start_time = time.time()
                self.downtime_start = time.time()
        
        if rc != 0:
            print(f"[Node A] 🔧 Unexpected disconnect! Attempting self-healing...")
            self.self_healing()
    
    def on_publish(self, client, userdata, mid):
        """Callback saat publish berhasil"""
        with self.lock:
            self.last_health_check = time.time()
            self.messages_sent += 1
            self._update_success_rate()
    
    def _update_success_rate(self):
        """Update message success rate"""
        total = self.messages_sent + self.messages_failed
        if total > 0:
            self.message_success_rate = (self.messages_sent / total) * 100
    
    def connect_to_broker(self, broker: str, port: int) -> bool:
        """Koneksi ke broker"""
        try:
            self.client = mqtt.Client(
                client_id=f"node_a_{int(time.time())}",
                callback_api_version=mqtt.CallbackAPIVersion.VERSION1
            )
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_publish = self.on_publish
            
            print(f"[Node A] 🔌 Connecting to {broker}:{port}...")
            self.client.connect(broker, port, keepalive=60)
            self.client.loop_start()
            
            # Wait for connection
            timeout = 5
            start_time = time.time()
            while not self.is_connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            return self.is_connected
        except Exception as e:
            print(f"[Node A] ❌ Connection error: {e}")
            return False
    
    def failover(self):
        """Failover ke broker backup"""
        failover_start = time.time()
        print(f"[Node A] 🔄 Initiating FAILOVER from Broker {self.current_broker}...")
        
        with self.lock:
            self.failover_count += 1
            if not self.failure_start_time:
                self.failure_start_time = time.time()
        
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
            failover_time = time.time() - failover_start
            print(f"[Node A] ✅ FAILOVER SUCCESS! Now using Broker {self.current_broker} "
                  f"(took {failover_time:.2f}s)")
            self.publish_status("failover", 
                               f"Failover to Broker {self.current_broker} in {failover_time:.2f}s")
            self.publish_metrics()
        else:
            print(f"[Node A] ❌ FAILOVER FAILED! Broker {self.current_broker} unavailable")
            time.sleep(2)
            self.failover()
    
    def self_healing(self):
        """Self-healing: restart koneksi saat stuck"""
        healing_start = time.time()
        print(f"[Node A] 🔧 Starting SELF-HEALING process...")
        
        with self.lock:
            self.reconnect_count += 1
            if not self.failure_start_time:
                self.failure_start_time = time.time()
        
        time.sleep(2)
        
        # Try reconnect ke broker saat ini
        if self.current_broker == "A":
            success = self.connect_to_broker(self.broker_primary, self.port_primary)
        else:
            success = self.connect_to_broker(self.broker_backup, self.port_backup)
        
        if not success:
            print(f"[Node A] ❌ Self-healing failed, attempting failover...")
            self.failover()
        else:
            healing_time = time.time() - healing_start
            print(f"[Node A] ✅ SELF-HEALING SUCCESS in {healing_time:.2f}s!")
            self.publish_status("self_healing", 
                               f"Self-healing completed in {healing_time:.2f}s")
            self.publish_metrics()
    
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
                "is_primary_active": self.is_primary_active,
                "timestamp": datetime.now().isoformat()
            }
            try:
                self.client.publish(self.topic_status, json.dumps(payload), qos=1)
            except Exception as e:
                print(f"[Node A] ❌ Publish status error: {e}")
    
    def publish_metrics(self):
        """Publish detailed metrics"""
        if self.client and self.is_connected:
            uptime = time.time() - self.uptime_start
            availability = ((uptime - self.total_downtime) / uptime * 100) if uptime > 0 else 0
            
            payload = {
                "node": "A",
                "recovery_metrics": {
                    "avg_recovery_time": round(self.avg_recovery_time, 2),
                    "fastest_recovery": round(self.fastest_recovery, 2) if self.fastest_recovery else None,
                    "slowest_recovery": round(self.slowest_recovery, 2) if self.slowest_recovery else None,
                    "recovery_count": len(self.recovery_times)
                },
                "message_metrics": {
                    "sent": self.messages_sent,
                    "failed": self.messages_failed,
                    "success_rate": round(self.message_success_rate, 2),
                    "avg_latency": round(self.avg_latency, 3)
                },
                "system_metrics": {
                    "uptime": round(uptime, 2),
                    "total_downtime": round(self.total_downtime, 2),
                    "availability": round(availability, 2)
                },
                "timestamp": datetime.now().isoformat()
            }
            try:
                self.client.publish(self.topic_metrics, json.dumps(payload), qos=1)
            except Exception as e:
                print(f"[Node A] ❌ Publish metrics error: {e}")
    
    def publish_sensor_data(self):
        """Publish data sensor dengan latency tracking"""
        if self.client and self.is_connected:
            send_time = time.time()
            payload = {
                "node": "A",
                "temperature": round(random.uniform(20.0, 35.0), 2),
                "humidity": round(random.uniform(40.0, 80.0), 2),
                "pressure": round(random.uniform(980.0, 1020.0), 2),
                "broker": self.current_broker,
                "send_time": send_time,
                "timestamp": datetime.now().isoformat()
            }
            try:
                result = self.client.publish(self.topic_data, json.dumps(payload), qos=1)
                if result.rc != mqtt.MQTT_ERR_SUCCESS:
                    print(f"[Node A] ❌ Publish failed with rc={result.rc}")
                    with self.lock:
                        self.messages_failed += 1
                        self._update_success_rate()
                    return False
                
                # Calculate latency (simulated)
                latency = time.time() - send_time
                with self.lock:
                    self.message_latencies.append(latency)
                    self.avg_latency = sum(self.message_latencies) / len(self.message_latencies)
                
                return True
            except Exception as e:
                print(f"[Node A] ❌ Publish data error: {e}")
                with self.lock:
                    self.messages_failed += 1
                    self._update_success_rate()
                return False
        else:
            with self.lock:
                self.messages_failed += 1
                self._update_success_rate()
        return False
    
    def sensor_thread(self):
        """Thread untuk simulasi sensor dan publish data"""
        print("[Node A] 📡 Sensor thread started")
        while self.running:
            if self.is_connected:
                success = self.publish_sensor_data()
                if not success:
                    print("[Node A] ⚠️ Sensor data publish failed")
            time.sleep(2)
    
    def health_check_thread(self):
        """Thread untuk monitoring kesehatan koneksi"""
        print("[Node A] 🏥 Health check thread started")
        while self.running:
            time.sleep(5)
            
            if not self.is_connected:
                print("[Node A] ⚠️ Health check: NOT CONNECTED - triggering failover")
                self.failover()
            else:
                with self.lock:
                    idle_time = time.time() - self.last_health_check
                
                if idle_time > 15:
                    print(f"[Node A] ⚠️ Health check: TIMEOUT ({idle_time:.1f}s) - triggering self-healing")
                    self.self_healing()
                else:
                    print(f"[Node A] ✅ Health OK | Broker: {self.current_broker} | "
                          f"Success Rate: {self.message_success_rate:.1f}% | "
                          f"Avg Recovery: {self.avg_recovery_time:.2f}s")
    
    def metrics_reporter_thread(self):
        """Thread untuk report metrics secara periodik"""
        print("[Node A] 📊 Metrics reporter started")
        while self.running:
            time.sleep(10)
            if self.is_connected:
                self.publish_metrics()
    
    def command_listener(self):
        """Listen for user commands to simulate failures"""
        print("[Node A] 🎮 Command listener started")
        while self.running:
            try:
                cmd = input().strip().lower()
                if cmd == 'crash':
                    self.simulate_crash()
                elif cmd == 'recover':
                    self.force_recovery()
                elif cmd == 'help':
                    print("\nAvailable commands:")
                    print("  crash   - Simulate Node A failure")
                    print("  recover - Force immediate recovery")
                    print("  help    - Show this help")
            except:
                pass
    
    def simulate_crash(self):
        """Simulate Node A crash for failover testing"""
        print("\n" + "="*70)
        print("💥 SIMULATING NODE A CRASH!")
        print("="*70)
        
        with self.lock:
            self.is_primary_active = False
            self.crash_simulation_enabled = True
        
        # Publish crash notification
        if self.client and self.is_connected:
            crash_payload = {
                "node": "A",
                "event": "CRASHED",
                "message": "Node A has CRASHED! Backup system should take over.",
                "is_primary_active": False,
                "timestamp": datetime.now().isoformat()
            }
            try:
                self.client.publish("/system/alert", json.dumps(crash_payload), qos=1)
                self.client.publish(self.topic_status, json.dumps(crash_payload), qos=1)
            except:
                pass
        
        # Disconnect and stop operations
        if self.client:
            try:
                self.client.loop_stop()
                self.client.disconnect()
            except:
                pass
        
        with self.lock:
            self.is_connected = False
        
        print(f"[Node A] ❌ PRIMARY NODE DOWN! Node B should activate as backup.")
        print(f"[Node A] ⏳ Will auto-recovery in {self.crash_recovery_time} seconds...\n")
        
        # Wait for recovery period
        time.sleep(self.crash_recovery_time)
        
        # Auto-recovery
        if self.crash_simulation_enabled:
            self.force_recovery()
    
    def force_recovery(self):
        """Force Node A to recover from crash"""
        if not self.crash_simulation_enabled:
            print("[Node A] ℹ️ Node is not in crashed state.")
            return
        
        print("\n" + "="*70)
        print("🔄 STARTING NODE A RECOVERY...")
        print("="*70)
        
        with self.lock:
            self.crash_simulation_enabled = False
            self.is_primary_active = True
        
        # Reconnect
        success = self.connect_to_broker(self.broker_primary, self.port_primary)
        
        if success:
            print("[Node A] ✅ RECOVERY SUCCESSFUL! Primary node is back online.")
            print("[Node A] 📡 Requesting data sync from Node B...\n")
            
            # Request data sync from Node B
            if self.client and self.is_connected:
                sync_request = {
                    "node": "A",
                    "event": "RECOVERY_COMPLETE",
                    "message": "Node A recovered. Requesting data sync from backup.",
                    "is_primary_active": True,
                    "request_sync": True,
                    "timestamp": datetime.now().isoformat()
                }
                try:
                    self.client.publish("/system/alert", json.dumps(sync_request), qos=1)
                    self.client.publish(self.topic_status, json.dumps(sync_request), qos=1)
                    self.client.publish("/nodeB/command", json.dumps({"command": "sync_data"}), qos=1)
                except:
                    pass
        else:
            print("[Node A] ❌ Recovery failed. Retrying...")
            time.sleep(2)
            self.force_recovery()
    
    def start(self):
        """Start Node A"""
        print("=" * 70)
        print("Node A - IoT Device with Failover & Self-Healing (IMPROVED)")
        print("=" * 70)
        
        # Connect ke broker primary
        success = self.connect_to_broker(self.broker_primary, self.port_primary)
        
        if not success:
            print("[Node A] ⚠️ Primary broker unavailable, trying backup...")
            self.failover()
        
        # Start threads
        sensor_t = threading.Thread(target=self.sensor_thread, daemon=True)
        health_t = threading.Thread(target=self.health_check_thread, daemon=True)
        metrics_t = threading.Thread(target=self.metrics_reporter_thread, daemon=True)
        
        sensor_t.start()
        health_t.start()
        metrics_t.start()
        
        print("[Node A] ✅ All threads started. Press Ctrl+C to stop.")
        print("\n📊 Improvements:")
        print("  - Recovery time tracking")
        print("  - Message success rate monitoring")
        print("  - System availability metrics")
        print("  - Detailed performance analytics")
        print("\n⚡ Failover Testing:")
        print("  - Type 'crash' to simulate Node A failure")
        print("  - Node B will take over as backup sensor")
        print("  - Node A will auto-recovery after 15 seconds\n")
        
        # Start command listener thread
        cmd_thread = threading.Thread(target=self.command_listener, daemon=True)
        cmd_thread.start()
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[Node A] 🛑 Stopping...")
            self.running = False
            if self.client:
                self.publish_status("shutdown", "Node A shutting down")
                self.publish_metrics()
                self.client.loop_stop()
                self.client.disconnect()
            
            # Print final statistics
            print("\n" + "=" * 70)
            print("FINAL STATISTICS")
            print("=" * 70)
            print(f"Uptime: {time.time() - self.uptime_start:.2f}s")
            print(f"Total Downtime: {self.total_downtime:.2f}s")
            print(f"Availability: {((time.time() - self.uptime_start - self.total_downtime) / (time.time() - self.uptime_start) * 100):.2f}%")
            print(f"Messages Sent: {self.messages_sent}")
            print(f"Messages Failed: {self.messages_failed}")
            print(f"Success Rate: {self.message_success_rate:.2f}%")
            print(f"Avg Recovery Time: {self.avg_recovery_time:.2f}s")
            print(f"Failovers: {self.failover_count}")
            print(f"Self-Healings: {self.reconnect_count}")
            print("=" * 70)
            print("[Node A] ✅ Stopped.")

if __name__ == "__main__":
    node = NodeAImproved()
    node.start()
