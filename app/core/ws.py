import asyncio
import uuid
from fastapi import WebSocket, WebSocketDisconnect
import redis.asyncio.client as rs

from app.api.deps import RedisClientDep
from app.core.redis import get_redis_client


class ConnectionManager:
    def __init__(self):
        # self.active_connections: dict[str, WebSocket] = {}
        print("ConnectionManager initialized")
        self.active_connections: dict[str, WebSocket] = {}
        self.redis_client = get_redis_client()
        self.pubsub = self.redis_client.pubsub()
        self.NODE_ID = uuid.uuid4()

    async def connect(self, websocket: WebSocket):
        uid = uuid.uuid4()
        user_id = str(uid)

        await websocket.accept()
        channel = str(self.NODE_ID)
        self.active_connections[user_id] = websocket
        asyncio.create_task(self.listen_for_messages(self.pubsub, websocket))
        await self.broadcast(f"User {user_id} connected")
        return user_id

    async def listen_for_messages(self, pubsub, websocket: WebSocket):
        try:
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                if message and message["type"] == "message":
                    await websocket.send_text(str(message["data"]))
                await asyncio.sleep(2)  # Prevent busy waiting
        except WebSocketDisconnect:
            await self.disconnect(websocket)

    async def disconnect(self, websocket: WebSocket):
        for user_id, (connection, pubsub) in list(self.active_connections.items()):
            if connection == websocket:
                del self.active_connections[user_id]
                print(f"Disconnected: {user_id}")
                await self.broadcast(f"User {user_id} disconnected")
                break
        await websocket.close()

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)

    async def publish_message(self, channel: str, message: str):
        await self.redis_client.publish(channel, message)

    async def subscribe_to_channel(self, channel: str):
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe(channel)
        return pubsub

    async def unsubscribe_from_channel(self, pubsub, channel: str):
        await pubsub.unsubscribe(channel)
        await pubsub.close()

    def get_active_connections(self):
        # keys
        print("Active connections:", self.active_connections.keys())
        return list(self.active_connections.keys())

    async def get_connection(self, user_id: str):
        return self.active_connections.get(user_id)

    async def get_user_id(self, websocket: WebSocket):
        for user_id, connection in self.active_connections.items():
            if connection == websocket:
                return user_id
        return None


connection_manager = ConnectionManager()
