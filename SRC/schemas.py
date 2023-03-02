from pydantic import BaseModel
from typing import Optional, List

class Map(BaseModel):
    user: str
    base64_image: str