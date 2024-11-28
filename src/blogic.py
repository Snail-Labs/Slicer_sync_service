from dataclasses import dataclass
from typing import List, Dict, Tuple
from fastapi import WebSocket
from fastapi import HTTPException
from fastapi import WebSocketException
from fastapi import status
from jsonpatch import JsonPatch


from external_api_calls import authenticate
from external_api_calls import retrieve_table


# Доступ
@dataclass
class Permission:
    subject_id: int
    object_id: int
    permition_level: str
    access: bool

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.permition_level == 'access_denined':
            self.access = False 
        else:
            self.access = True
 

# Пользователь
@dataclass
class User:
    id: int

# Стол
@dataclass
class Table:
    schema: dict

    async def add_user(self, user_id: int) -> JsonPatch:
        ...

    async def remove_user(self, user_id: int) -> JsonPatch:
        ...

# Группа
@dataclass
class Group:
    id: int
    socket_list: List[WebSocket]
    permition_list: List[Permission]
    table: Table

    async def validate_permition():
        ...

    async def validate_patch():
        ...


# Менеджер Групп
@dataclass
class GroupManager:
    group_dict: Dict[int, Group]


    async def broadcast(self, sender: WebSocket, message: JsonPatch) -> None:
        group_id = sender.headers.get("GroupId")

        for socket in self.group_dict[group_id].socket_list:
            if socket != sender:
                await socket.send_text(message)


    async def connect(self, socket: WebSocket):
        group_id = socket.headers.get("GroupId")
        user_id = socket.headers.get("UserId")

        # Авторизация
        permition_level = await authenticate(group_id=group_id,
                                             user_id=user_id,)
        permission = Permission(subject_id=group_id,
                                object_id=user_id,
                                permition_level=permition_level)
        # Если не прошли авторизацию
        if permission.access == False:
            raise WebSocketException(code=status.HTTP_401_UNAUTHORIZED,
                                     reason="permition denied")
        
        # Проверяем существует ли группа с таким ID в списке активных
        group_exists = (group_id in self.group_dict)

        # Если группа не отслеживается
        if not group_exists:
            table = await retrieve_table(group_id=group_id)
            group = Group(id=group_id,
                          permition_list=[],
                          socket_list=[],
                          table=table)
            self.group_dict[group_id]=group
        
        # Обновляем группу
        self.group_dict[group_id].socket_list.append(socket)
        self.group_dict[group_id].permition_list.append(permission)

        # Обновляем схему
        patch = await self.group_dict[group_id].table.add_user(user_id=user_id)

        # Отправляем стол подключенному гостю
        await socket.send_json(data=self.group_dict[group_id].table.schema)

        # Выполняем рассылку остальным участникам
        await self.broadcast(sender=socket, message=patch)


    async def disconect(self, socket: WebSocket):
        group_id = socket.headers.get("GroupId")
        user_id = socket.headers.get("UserId")

        # Обновляем схему
        patch = await self.group_dict[group_id].table.remove_user(user_id=user_id)

        # Выполняем рассылку остальным участникам
        await self.broadcast(sender=socket, message=patch)

        # Удаляем сокет ихз группы
        self.group_dict[group_id].socket_list.remove(socket)
        if len(self.group_dict[group_id].socket_list) == 0:
            del self.group_dict[group_id]

        
    async def process_patch(self, socket: WebSocket, patch: JsonPatch):
        ...

    async def apply_patch(self, socket: WebSocket, patch: JsonPatch):
        ...
