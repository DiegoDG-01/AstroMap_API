from pydantic import BaseModel
from typing import Optional, List


class Map_Schema(BaseModel):
    MapUID: str
    UserUID: str
    Location: str
    Date_Time: str
