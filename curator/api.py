from typing import Annotated
from fastapi import Depends, FastAPI
from sqlalchemy import select
from sqlmodel import Session
from curator.data_model import ImageLocation, create_db_and_tables, db_session

SessionDep = Annotated[Session, Depends(db_session)]

app = FastAPI()

@app.on_event("startup")
def on_startup():
    """
    Startup event handler to create the database and tables.
    """
    create_db_and_tables()

@app.get("/locations")
async def get_locations(session: SessionDep) -> list[ImageLocation]:
    """
    Retrieves all import locations from the database.
    
    Returns:
        list: A list of import locations.
    """
    locations = session.exec(select(ImageLocation)).all()
    return locations