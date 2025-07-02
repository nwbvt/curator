from typing import List, Optional
from sqlalchemy import String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Image(Base):
    __tablename__ = "image"

    id: Mapped[int] = mapped_column(primary_key=True)
    location: Mapped[str] = mapped_column(String())
    hash: Mapped[str] = mapped_column(String(32))
    description: Mapped[Optional[str]] = mapped_column(String(256))

def connect(config: dict) -> None:
    """Connect to the database."""
    url= config["db"]
    engine = create_engine(url, echo=True)
    Base.metadata.create_all(engine)