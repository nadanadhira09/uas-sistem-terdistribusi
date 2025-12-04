"""
Node C - Attacker/Stress Tester
Fitur:
- Publish Flood (ribuan pesan per detik)
- Topic spam attack
- Delayed ACK simulation
- Multi-threading untuk serangan paralel
"""

import paho.mqtt.client as mqtt
import json
import time
import random
import threading
from datetime import datetime
from typing import Optional

class NodeCAttacker:
    def __init__(self):
        self.broker = "localhost"
        self.port = 1883
        self.clients = []
        self.running = True
        self.attack_active = False
        self.lock = threading.Lock()
        
        # Attack statistics
        self.total_messages_sent = 0
        self.messages_per_second = 0
        self.topics_created = 0
        self.attack_duration = 0
        
        # Attack configuration
        self.flood_rate = 10000  # messages per second
        self.num_threads = 10
        self.spam_topics_count = 100
        
        # Topics
        self.topic_status = "/nodeC/attack_status"
        self.main_client: Optional[mqtt.Client] = None
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback saat koneksi berhasil"""
        if rc == 0:
            print(f"[Node C] Attack client connected (rc={rc})")
        else:
            print(f"[Node C] Connection failed with code {rc}")
    
    def on_publish(self, client, userdata, mid):
        """Callback saat publish berhasil"""
        with self.lock:
            self.total_messages_sent += 1
    
    def connect_main_client(self) -> bool:
        """Koneksi client utama untuk status"""
        try:
            self.main_client = mqtt.Client(client_id=f"node_c_main_{int(time.time())}")
            self.main_client.on_connect = self.on_connect
            self.main_client.on_publish = self.on_publish
            
            print(f"[Node C] Connecting to {self.broker}:{self.port}...")
            self.main_client.connect(self.broker, self.port, keepalive=60)
            self.main_client.loop_start()
            
            time.sleep(2)
            return True
        except Exception as e:
            print(f"[Node C] Connection error: {e}")
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
                "timestamp": datetime.now().isoformat()
            }
            try:
                self.main_client.publish(self.topic_status, json.dumps(payload), qos=0)
            except Exception as e:
                print(f"[Node C] Publish status error: {e}")
    
    def flood_attack_worker(self, worker_id: int, messages_per_worker: int):
        """Worker thread untuk flood attack"""
        try:
            # Buat client untuk worker ini
            client = mqtt.Client(client_id=f"attacker_{worker_id}_{int(time.time())}")
            client.connect(self.broker, self.port, keepalive=60)
            client.loop_start()
            
            print(f"[Node C] Attack worker {worker_id} started (target: {messages_per_worker} msg/s)")
            
            messages_sent = 0
            start_time = time.time()
            
            while self.attack_active and self.running:
                # Publish flood messages
                for _ in range(messages_per_worker):
                    if not self.attack_active:
                        break
                    
                    topic = f"/attack/flood/worker_{worker_id}"
                    payload = {
                        "worker": worker_id,
                        "seq": messages_sent,
                        "data": "x" * 100,  # 100 bytes payload
                        "timestamp": time.time()
                    }
                    
                    try:
                        client.publish(topic, json.dumps(payload), qos=0)
                        messages_sent += 1
                    except:
                        pass
                
                # Control rate (1 detik)
                elapsed = time.time() - start_time
                if elapsed < 1.0:
                    time.sleep(1.0 - elapsed)
                
                start_time = time.time()
            
            client.loop_stop()
            client.disconnect()
            print(f"[Node C] Attack worker {worker_id} stopped (sent: {messages_sent} messages)")
            
        except Exception as e:
            print(f"[Node C] Worker {worker_id} error: {e}")
    
    def topic_spam_attack(self):
        """Spam banyak topic berbeda"""
        try:
            client = mqtt.Client(client_id=f"spam_attacker_{int(time.time())}")
            client.connect(self.broker, self.port, keepalive=60)
            client.loop_start()
            
            print(f"[Node C] Topic spam attack started (creating {self.spam_topics_count} topics)")
            
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
                    client.publish(topic, json.dumps(payload), qos=0)
                    with self.lock:
                        self.topics_created += 1
                except:
                    pass
                
                time.sleep(0.01)  # 10ms per topic
            
            print(f"[Node C] Topic spam attack completed ({self.topics_created} topics created)")
            
            client.loop_stop()
            client.disconnect()
            
        except Exception as e:
            print(f"[Node C] Topic spam error: {e}")
    
    def delayed_ack_attack(self):
        """Simulasi delayed ACK - publish dengan QoS 2 dan delay response"""
        try:
            client = mqtt.Client(client_id=f"delayed_ack_{int(time.time())}")
            
            # Custom callback untuk delay ACK
            def on_message(client, userdata, msg):
                time.sleep(1)  # Delay 1 detik sebelum ACK
            
            client.on_message = on_message
            client.connect(self.broker, self.port, keepalive=60)
            client.subscribe("/test/#", qos=2)
            client.loop_start()
            
            print(f"[Node C] Delayed ACK attack started")
            
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
            
            print(f"[Node C] Delayed ACK attack completed ({count} messages)")
            
            client.loop_stop()
            client.disconnect()
            
        except Exception as e:
            print(f"[Node C] Delayed ACK error: {e}")
    
    def monitor_attack_stats(self):
        """Monitor dan report statistik serangan"""
        print("[Node C] Attack statistics monitor started")
        
        last_count = 0
        
        while self.running:
            time.sleep(1)
            
            if self.attack_active:
                with self.lock:
                    current_count = self.total_messages_sent
                    self.messages_per_second = current_count - last_count
                    last_count = current_count
                    self.attack_duration += 1
                
                print(f"[Node C] Attack Stats: {self.messages_per_second} msg/s | "
                      f"Total: {self.total_messages_sent} | "
                      f"Topics: {self.topics_created} | "
                      f"Duration: {self.attack_duration}s")
                
                self.publish_attack_status("attacking", {
                    "rate": self.messages_per_second,
                    "duration": self.attack_duration
                })
    
    def start_attack(self, attack_type: str = "all"):
        """Start serangan"""
        print("\n" + "=" * 60)
        print(f"[Node C] Starting {attack_type.upper()} attack...")
        print("=" * 60 + "\n")
        
        with self.lock:
            self.attack_active = True
            self.total_messages_sent = 0
            self.messages_per_second = 0
            self.topics_created = 0
            self.attack_duration = 0
        
        threads = []
        
        if attack_type in ["flood", "all"]:
            # Flood attack dengan multiple workers
            messages_per_worker = self.flood_rate // self.num_threads
            for i in range(self.num_threads):
                t = threading.Thread(
                    target=self.flood_attack_worker,
                    args=(i, messages_per_worker),
                    daemon=True
                )
                threads.append(t)
                t.start()
        
        if attack_type in ["spam", "all"]:
            # Topic spam attack
            t = threading.Thread(target=self.topic_spam_attack, daemon=True)
            threads.append(t)
            t.start()
        
        if attack_type in ["delayed", "all"]:
            # Delayed ACK attack
            t = threading.Thread(target=self.delayed_ack_attack, daemon=True)
            threads.append(t)
            t.start()
        
        self.publish_attack_status("started", {"type": attack_type})
        
        return threads
    
    def stop_attack(self):
        """Stop serangan"""
        print("\n[Node C] Stopping attack...")
        with self.lock:
            self.attack_active = False
        
        time.sleep(2)
        
        self.publish_attack_status("stopped", {
            "total_messages": self.total_messages_sent,
            "duration": self.attack_duration
        })
        
        print(f"[Node C] Attack stopped. Total messages sent: {self.total_messages_sent}")
    
    def interactive_menu(self):
        """Menu interaktif untuk kontrol serangan"""
        print("\n" + "=" * 60)
        print("Node C - Attack Controller Menu")
        print("=" * 60)
        print("1. Start FLOOD Attack (10,000 msg/s)")
        print("2. Start TOPIC SPAM Attack")
        print("3. Start DELAYED ACK Attack")
        print("4. Start ALL Attacks")
        print("5. Stop Current Attack")
        print("6. Show Statistics")
        print("0. Exit")
        print("=" * 60)
    
    def start(self):
        """Start Node C dengan menu interaktif"""
        print("=" * 60)
        print("Node C - Attack/Stress Test Controller")
        print("=" * 60)
        
        # Connect main client
        success = self.connect_main_client()
        if not success:
            print("[Node C] Failed to connect to broker!")
            return
        
        # Start monitor thread
        monitor_t = threading.Thread(target=self.monitor_attack_stats, daemon=True)
        monitor_t.start()
        
        self.publish_attack_status("ready", {"message": "Attack controller ready"})
        
        attack_threads = []
        
        try:
            while self.running:
                self.interactive_menu()
                
                try:
                    choice = input("\nSelect option: ").strip()
                except EOFError:
                    choice = "0"
                
                if choice == "1":
                    if not self.attack_active:
                        attack_threads = self.start_attack("flood")
                    else:
                        print("[Node C] Attack already running!")
                
                elif choice == "2":
                    if not self.attack_active:
                        attack_threads = self.start_attack("spam")
                    else:
                        print("[Node C] Attack already running!")
                
                elif choice == "3":
                    if not self.attack_active:
                        attack_threads = self.start_attack("delayed")
                    else:
                        print("[Node C] Attack already running!")
                
                elif choice == "4":
                    if not self.attack_active:
                        attack_threads = self.start_attack("all")
                    else:
                        print("[Node C] Attack already running!")
                
                elif choice == "5":
                    if self.attack_active:
                        self.stop_attack()
                        for t in attack_threads:
                            t.join(timeout=3)
                        attack_threads = []
                    else:
                        print("[Node C] No attack is running!")
                
                elif choice == "6":
                    print("\n" + "=" * 60)
                    print("Attack Statistics")
                    print("=" * 60)
                    print(f"Total Messages Sent: {self.total_messages_sent}")
                    print(f"Current Rate: {self.messages_per_second} msg/s")
                    print(f"Topics Created: {self.topics_created}")
                    print(f"Attack Duration: {self.attack_duration}s")
                    print(f"Status: {'ATTACKING' if self.attack_active else 'IDLE'}")
                    print("=" * 60 + "\n")
                
                elif choice == "0":
                    break
                
                else:
                    print("[Node C] Invalid option!")
                
                time.sleep(0.5)
        
        except KeyboardInterrupt:
            print("\n[Node C] Interrupted!")
        
        finally:
            print("\n[Node C] Shutting down...")
            self.running = False
            if self.attack_active:
                self.stop_attack()
            
            if self.main_client:
                self.main_client.loop_stop()
                self.main_client.disconnect()
            
            print("[Node C] Stopped.")

if __name__ == "__main__":
    attacker = NodeCAttacker()
    attacker.start()
