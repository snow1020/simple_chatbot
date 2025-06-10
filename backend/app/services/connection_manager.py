# Contents for backend/app/services/connection_manager.py
from typing import Set

class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[str] = set()
        print("ConnectionManager initialized.")

    async def connect(self, sid: str):
        self.active_connections.add(sid)
        print(f"ConnectionManager: Client {sid} connected. Total: {len(self.active_connections)}")

    async def disconnect(self, sid: str):
        self.active_connections.discard(sid)
        print(f"ConnectionManager: Client {sid} disconnected. Total: {len(self.active_connections)}")

    def get_active_sids(self) -> Set[str]:
        return self.active_connections

manager = ConnectionManager()
