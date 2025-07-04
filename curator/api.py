import asyncio
from typing import Annotated
from fastapi import Body, Depends, FastAPI
from sqlmodel import Session, select
from curator import loader
from curator.data_model import Image, ImageLocation, create_db_and_tables, db_session

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

@app.post("/locations")
async def add_location(directory: Annotated[str, Body(embed=True)],
                       session: SessionDep) -> ImageLocation:
    """
    Adds a new import location to the database.
    
    Args:
        location (ImageLocation): The import location to add.
    """
    location = ImageLocation(directory=directory)
    session.add(location)
    session.commit()
    session.refresh(location)
    return location

@app.get("/images")
async def get_images(session: SessionDep) -> list[Image]:
    """
    Retrieves all images from the database.
    
    Returns:
        list: A list of images.
    """
    images = session.exec(select(Image)).all()
    return images       