from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id         : Optional[int] = Field(default=None, primary_key=True)
    username   : str        = Field(index=True, unique=True)
    email      : str
    full_name  : str
    hashed_pw  : str
    firebase_uid: Optional[str] = Field(default=None, index=True, unique=True)
    created_at : datetime   = Field(default_factory=datetime.utcnow)
