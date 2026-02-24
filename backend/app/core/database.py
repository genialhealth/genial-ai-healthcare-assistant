from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
import os

# Create the database URL
# Allow overriding the directory using DB_DIR for Docker volume mapping
db_filename = "gt-data.db"
if os.getenv("BUILD") != "production":
    db_filename = "gt-data-dev.db"

# Default to app/ directory if DB_DIR is not set
default_dir = os.path.dirname(os.path.dirname(__file__))
db_dir = os.getenv("DB_DIR", default_dir)

# Ensure the directory exists
os.makedirs(db_dir, exist_ok=True)

DB_PATH = os.path.join(db_dir, db_filename)
SQLALCHEMY_DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

# Create Async Engine
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}, # Needed for SQLite
    echo=False # Set to True to log SQL queries
)

# Create Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base Class for Models
class Base(DeclarativeBase):
    pass

# Dependency to get DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
