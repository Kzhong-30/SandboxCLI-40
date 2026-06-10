from typing import Dict, List
from fastapi import WebSocket
import json


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, monitor_id: str, websocket: WebSocket):
        await websocket.accept()
        if monitor_id not in self.active_connections:
            self.active_connections[monitor_id] = []
        self.active_connections[monitor_id].append(websocket)

    def disconnect(self, monitor_id: str, websocket: WebSocket):
        if monitor_id in self.active_connections:
            self.active_connections[monitor_id].remove(websocket)
            if not self.active_connections[monitor_id]:
                del self.active_connections[monitor_id]

    async def send_alert(self, monitor_id: str, alert_data: dict):
        if monitor_id in self.active_connections:
            message = json.dumps(alert_data, ensure_ascii=False, default=str)
            dead_connections = []
            for connection in self.active_connections[monitor_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    dead_connections.append(connection)
            for conn in dead_connections:
                self.disconnect(monitor_id, conn)

    async def broadcast(self, alert_data: dict):
        message = json.dumps(alert_data, ensure_ascii=False, default=str)
        for monitor_id in list(self.active_connections.keys()):
            dead_connections = []
            for connection in self.active_connections[monitor_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    dead_connections.append(connection)
            for conn in dead_connections:
                self.disconnect(monitor_id, conn)


manager = ConnectionManager()
