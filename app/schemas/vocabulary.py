from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class VocabIn(BaseModel):
    word: str
    meaning: str
    example: Optional[str] = None

class VocabOut(VocabIn):
    id        : int
    created_at: datetime