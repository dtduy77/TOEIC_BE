from sqlmodel import SQLModel
from app.db.session import engine
from app import models  # noqa: F401  (pulls in tables via import side‑effect)

def init_db() -> None:
    SQLModel.metadata.create_all(engine)
