from pydantic import BaseModel
from typing import List, Optional, Union, Dict
from fastapi import WebSocket
from jsonpatch import JsonPatch
from dataclasses import dataclass
from models import Table


class ReversableJsonPatch(JsonPatch):
    def __init__(self, *args, **kwargs):
        super.__init__(*args, **kwargs)
        self.reversed_patch: JsonPatch = None

    def _make_reverse(self, src, dst) -> JsonPatch:
        return self.from_diff(src, dst)
    
    def apply(self, src):
        dst = self.apply(src)
        self.reversed_patch = self._make_reverse(src, dst)
    
    def reverse(self, src):
        return self.reversed_patch.apply(src)
    


class Journal:
    def __init__(self):
        self.patch_list: List[ReversableJsonPatch] = []
        self.undo_patch_list: List[ReversableJsonPatch] = []

    def apply_patch(self, patch: ReversableJsonPatch, src):
        dst = patch.apply(src)
        self.patch_list.append(patch)
        return dst
    
    def undo_patch(self, src):
        undo_patch = self.patch_list.pop()
        self.undo_patch_list.append(undo_patch)
        dst = undo_patch.reverse(src)
        return dst

    def redo_patch(self, src):
        redo_patch = self.undo_patch_list.pop()
        self.patch_list.append(redo_patch)
        dst = redo_patch.apply(src)
        return dst



 
@dataclass
class GroupConnection:
    sockets: List[WebSocket]
    table: Table
    journals: Dict[str, Journal]

    

class GroupConnectionManager:
    def __init__(self):
        self.groups: Dict[str, GroupConnection] = {}   

    async def connect(self, websocket: WebSocket):
        group_id = websocket.headers.get("GroupId")

        # Инициализация GroupConnection
        if group_id not in self.groups:
            # Ходим в сервис со столами за моделью
            table = await Table.get_by_id(table_id=group_id)

            group_connection = GroupConnection(
                sockets=[],
                journals=dict(),
                table=table
            )
            self.groups[group_id] = group_connection
        self.groups[group_id].sockets.append(websocket)

        # Инициализация состояния стола при первом подключении
        await websocket.send_json(self.groups[group_id].table)

    async def disconect(self, websocket: WebSocket):
        group_id = websocket.headers.get("GroupId")

        self.groups[group_id].sockets.remove(websocket)

        if len(self.groups[group_id].sockets) == 0:
            del self.groups[group_id]

    async def broadcast(self, sender: WebSocket, message: str):
        group_id = sender.headers.get("GroupId")

        for conn in self.groups[group_id].sockets:
            if conn != sender:
                await conn.send_text(message)

    
