from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class Vocabulary(SQLModel, table=True):
    id        : Optional[int] = Field(default=None, primary_key=True)
    user_id   : int        = Field(foreign_key="user.id", index=True)
    word      : str
    meaning   : str
    example   : Optional[str] = None
    created_at: datetime   = Field(default_factory=datetime.utcnow)
