import logging
from typing import Optional

from fastapi import WebSocket

from app.models.user import User

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket client connections and broadcasting."""

    def __init__(self):
        self.active_connections: dict[WebSocket, Optional[User]] = {}

    async def add(self, websocket: WebSocket, user: Optional[User] = None):
        self.active_connections[websocket] = user

    async def remove(self, websocket: WebSocket):
        self.active_connections.pop(websocket, None)

    async def broadcast(self, message: dict):
        disconnected = []
        for ws in list(self.active_connections):
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            await self.remove(ws)


connection_manager = ConnectionManager()
