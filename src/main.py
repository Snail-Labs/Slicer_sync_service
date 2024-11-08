from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List, Dict

app = FastAPI()

# Хранилище для сокетов, организованных по Group_Id
connections: Dict[str, List[WebSocket]] = {}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    group_id = websocket.headers.get("X-Group-Id")
    user_id = websocket.headers.get("X-User-Id")

    if group_id is None or user_id is None:
        await websocket.close()
        return

    if group_id not in connections:
        connections[group_id] = []
    connections[group_id].append(websocket)


    try:
        await websocket.accept()
        while True:
            data = await websocket.receive_text()
            message = f"User {user_id} sent: {data}"

            for conn in connections[group_id]:
                if conn != websocket:
                    await conn.send_text(message)
    except WebSocketDisconnect:
        connections[group_id].remove(websocket)
        if len(connections[group_id]) == 0:
            del connections[group_id]