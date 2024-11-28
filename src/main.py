from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi import FastAPI, HTTPException
from jsonschema import validate, ValidationError
import json
import os
import uvicorn
from models import (
    Table, 
    User,
    Model,
    Printer,
)
from connection_manager import (
    GroupConnectionManager
)
from jsonschema import RefResolver
from jsonpatch import JsonPatch


# Настройки
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_DIR = os.path.join(BASE_DIR, 'schemas')


# FastApi App
app = FastAPI()
# Меннеджер подключенийы
connection_manager = GroupConnectionManager()





@app.websocket("/ws")
async def websocket_endpoint(socket: WebSocket):
    group_id = socket.headers.get("GroupId")
    user_id = socket.headers.get("UserId")

    if group_id is None or user_id is None:
        await socket.close()
        return

    await connection_manager.connect(socket=socket)

    # Работа в сокете
    try:
        await socket.accept()
        while True:
            # Принимаем патч
            json_patch = await socket.receive_json()
            
            # Валидируем патч
            patch = JsonPatch(patch=json_patch)
            validated_patch = await connection_manager.process_patch(socket=socket, patch=patch)

            # Применяем патч
            await connection_manager.apply_patch(socket=socket, patch=validated_patch)

            # Рассылаем изменения
            await connection_manager.broadcast(sender=socket, message=validated_patch)
    except WebSocketDisconnect:
        await connection_manager.disconect(socket=socket)










@app.put("/api/validate/table")
async def validate_json(data: Table):
    with open(os.path.join(SCHEMA_DIR, "table.schema.json")) as f:
        schema = json.load(f)
    resolver = RefResolver(base_uri='file://' + SCHEMA_DIR + '/', referrer=schema)

    # Валидация на уровне json схемы
    try:
        validate(instance=data.model_dump(), schema=schema, resolver=resolver)
    except ValidationError as e: 
        raise HTTPException(status_code=400, detail=f"Validation error: {e.message}")
    
    # Валидация на уровне бизнес логики


    return {"message": "JSON is valid!"}


@app.put("/api/validate/printer")
async def validate_json(data: Printer):
    with open(os.path.join(SCHEMA_DIR, "printer.schema.json")) as f:
        schema = json.load(f)
    resolver = RefResolver(base_uri='file://' + SCHEMA_DIR + '/', referrer=schema)

    # Валидация на уровне json схемы
    try:
        validate(instance=data.model_dump(), schema=schema, resolver=resolver)
    except ValidationError as e: 
        raise HTTPException(status_code=400, detail=f"Validation error: {e.message}")
    
    # Валидация на уровне бизнес логики


    return {"message": "JSON is valid!"}



@app.put("/api/validate/model")
async def validate_json(data: Model):
    with open(os.path.join(SCHEMA_DIR, "model.schema.json")) as f:
        schema = json.load(f)
    resolver = RefResolver(base_uri='file://' + SCHEMA_DIR + '/', referrer=schema)

    # Валидация на уровне json схемы
    try:
        validate(instance=data.model_dump(), schema=schema, resolver=resolver)
    except ValidationError as e: 
        raise HTTPException(status_code=400, detail=f"Validation error: {e.message}")
    
    # Валидация на уровне бизнес логики


    return {"message": "JSON is valid!"}





if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
