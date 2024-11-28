from pydantic import BaseModel
from typing import List, Optional, Union, Dict
from fastapi import WebSocket
from jsonpatch import JsonPatch


class Support(BaseModel):
    support_type: str


class User(BaseModel):
    id: int
    name: str


class Model(BaseModel):
    id: int
    file: str
    x: float
    y: float
    z: float
    x_scale: float
    y_scale: float
    z_scale: float
    x_angle: float
    y_angle: float
    z_angle: float
    support: Support


class Printer(BaseModel):
    id: int
    name: str
    print_config: str


class Table(BaseModel):
    users: List[User]
    models: List[Model]
    selected_models: Optional[list] = None
    printer: Optional[Printer] = None

    def get_by_id(table_id: int|str):
        return Table()



