import requests
import os
import json
from threading import Thread
import time

class ServerSync:
    def __init__(self, server_name, other_servers):
        self.server_name = server_name
        self.other_servers = other_servers  # List of other server URLs
        self.sync_interval = 30  # seconds
        
    def start_periodic_sync(self):
        """Start background thread for periodic synchronization"""
        thread = Thread(target=self._sync_loop, daemon=True)
        thread.start()
        print(f"{self.server_name}: Started periodic sync thread")
    
    def _sync_loop(self):
        """Periodically sync with other servers"""
        while True:
            time.sleep(self.sync_interval)
            self.sync_with_peers()
    
    def sync_with_peers(self):
        """Sync user lists and health status with peer servers"""
        print(f"{self.server_name}: Syncing with peer servers...")
        
        for server_url in self.other_servers:
            try:
                response = requests.get(
                    f"{server_url}/api/sync", 
                    timeout=3,
                    params={"requesting_server": self.server_name}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"Synced with {data['server']}: {data['users']} users, {data['messages']} messages")
                else:
                    print(f"Sync failed with {server_url}: HTTP {response.status_code}")
                    
            except requests.RequestException as e:
                print(f"Could not reach {server_url}: {e}")
    
    def notify_peers(self, event_type, data):
        """Notify other servers of an event (user join/leave, etc.)"""
        for server_url in self.other_servers:
            try:
                requests.post(
                    f"{server_url}/api/event",
                    json={
                        "source_server": self.server_name,
                        "event_type": event_type,
                        "data": data
                    },
                    timeout=2
                )
            except requests.RequestException:
                pass  # Best effort notification