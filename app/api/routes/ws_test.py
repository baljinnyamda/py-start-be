from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import RedisClientDep
from app.core.ws import connection_manager

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
    await connection_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data.startswith("{") and data.endswith("}"):
                import json

                try:
                    json_data = json.loads(data)
                    user_id = json_data.get("user_id")
                    print(f"Received JSON data: {json_data}")
                    await connection_manager.publish_message(
                        user_id, json.dumps(json_data)
                    )
                except json.JSONDecodeError:
                    await connection_manager.send_personal_message(
                        "Invalid JSON format", websocket
                    )
            else:
                # Process non-JSON data here
                await connection_manager.publish_message("ws", data)

    except WebSocketDisconnect:
        await connection_manager.disconnect(websocket)
        await redis_client.close()


@router.get("/all-connections")
async def get_all_connections(redis_client: RedisClientDep):
    connections = connection_manager.active_connections
    return {"connections": list(connections.keys())}
