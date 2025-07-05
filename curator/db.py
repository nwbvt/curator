from typing import Iterable
from sqlalchemy import Engine, create_engine
from sqlmodel import Session, SQLModel
from curator.config import settings

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