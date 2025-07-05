from contextlib import contextmanager
from typing import Iterable
from sqlalchemy import Engine, create_engine
from sqlmodel import Field, Session, SQLModel
from curator.config import settings

class Image(SQLModel, table=True):
    """Model representing an image."""
    
    id: int | None = Field(default=None, primary_key=True)
    location: str = Field(unique=True)
    hash: str = Field(index=True, max_length=31)
    description: str | None = None
    format: str = Field(max_length=3)

class ImageLocation(SQLModel, table=True):
    """Model representing an import location for images."""
    
    id: int | None = Field(default=None, primary_key=True)
    directory: str = Field(unique=True)

def db_engine() -> Engine:
    """Create and return a database engine."""
    return create_engine(settings.db_url, echo=settings.db_echo)

def create_db_and_tables():
    """Create the database and tables if they do not exist."""
    SQLModel.metadata.create_all(db_engine())

def db_session() -> Iterable[Session]:
    """Create a new database session."""
    engine = db_engine()
    return Session(engine)