from datetime import datetime
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str
    email   : str
    full_name: str

class UserOut(BaseModel):
    id       : int
    username : str
    email    : str
    full_name: str
    created_at: datetime