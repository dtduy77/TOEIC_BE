from sqlmodel import create_engine, Session
from app.core.config import get_settings
from sqlalchemy.pool import QueuePool

settings = get_settings()

# Configure connection arguments based on database type
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

# Create engine with appropriate pooling for PostgreSQL
if settings.DATABASE_URL.startswith("postgresql"):
    engine = create_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_size=5,               # Number of connections to keep open
        max_overflow=10,           # Max number of connections to create beyond pool_size
        pool_timeout=30,           # Seconds to wait before timing out on getting a connection
        pool_recycle=1800,         # Recycle connections after 30 minutes
        pool_pre_ping=True,        # Verify connections before using them
        poolclass=QueuePool       # Use QueuePool for PostgreSQL
    )
else:
    engine = create_engine(settings.DATABASE_URL, echo=False, connect_args=connect_args)

def get_session():
    with Session(engine) as session:
        yield session
