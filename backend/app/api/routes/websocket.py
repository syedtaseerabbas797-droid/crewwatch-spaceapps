import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.integrations.redis_client import get_redis

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Real-time Feeds"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        async with self._lock:
            dead_connections = []
            for connection in self.active_connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.warning(f"Error sending to WebSocket client: {e}")
                    dead_connections.append(connection)
            for dead in dead_connections:
                if dead in self.active_connections:
                    self.active_connections.remove(dead)

manager = ConnectionManager()

@router.websocket("/ws/mission-feed")
async def websocket_mission_feed(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Initial greeting message
        await websocket.send_json({
            "type": "CONNECTED",
            "message": "Connected to CrewWatch live astronaut telemetry feed",
        })
        while True:
            # Keep socket alive and listen for client pings
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "PING":
                    await websocket.send_json({"type": "PONG"})
            except Exception:
                pass
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket unexpected error: {e}")
        await manager.disconnect(websocket)

async def redis_listener():
    """Background subscriber for Redis pub/sub to fan-out to WebSocket clients."""
    while True:
        try:
            r = await get_redis()
            if r:
                pubsub = r.pubsub()
                await pubsub.subscribe("mission:feed")
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        try:
                            payload = json.loads(message["data"])
                            await manager.broadcast(payload)
                        except Exception as e:
                            logger.error(f"Error forwarding Redis msg: {e}")
            else:
                await asyncio.sleep(3)
        except Exception as e:
            logger.warning(f"Redis listener disconnected ({e}), retrying in 3s...")
            await asyncio.sleep(3)
