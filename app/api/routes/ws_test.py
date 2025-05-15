import uuid

from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import HTMLResponse

from app.api.deps import RedisClientDep
from app.core.ws import websocket_conn_man

router = APIRouter(prefix="/ws-test", tags=["ws-test"])

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/api/v1/ws-test/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


@router.get("/")
async def get():
    return HTMLResponse(html)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, redis_client: RedisClientDep):
    user_id = str(uuid.uuid4())
    try:
        await websocket_conn_man.connect(websocket, user_id)
        print(f"User connected: {user_id}")
        await websocket_conn_man.broadcast(f"CLIENT JOINED: {user_id}")

        while True:
            data = await websocket.receive_text()
            await websocket_conn_man.broadcast(f"Client #{user_id} says: {data}")
            print(f"Message from {user_id}: {data}")
    except WebSocketDisconnect:
        print(f"User disconnected: {user_id}")
        websocket_conn_man.disconnect(user_id)
        await websocket_conn_man.broadcast(f"CLIENT LEFT: {user_id}")


@router.get("/all-connections")
async def get_all_connections(redis_client: RedisClientDep):
    connections = websocket_conn_man.active_connections
    return {"connections": list(connections.keys())}
