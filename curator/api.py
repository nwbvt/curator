import logging as log
from typing import Annotated
from fastapi import BackgroundTasks, Body, Depends, FastAPI, HTTPException
from sqlmodel import Session, select
from curator.data_model import Image, ImageLocation, create_db_and_tables, db_session
from curator.loader import load_from_directory

SessionDep = Annotated[Session, Depends(db_session)]

app = FastAPI()

@app.on_event("startup")
def on_startup():
    """
    Startup event handler to create the database and tables.
    """
    create_db_and_tables()
    log.basicConfig(level=log.INFO)

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
                       session: SessionDep,
                       tasks: BackgroundTasks) -> ImageLocation:
    """
    Adds a new import location to the database.
    
    Args:
        location (ImageLocation): The import location to add.
    """
    location = ImageLocation(directory=directory)
    if session.exec(select(ImageLocation).where(ImageLocation.directory == directory)).first():
        raise HTTPException(status_code=400, detail=f"Location '{directory}' already exists.")
    session.add(location)
    session.commit()
    session.refresh(location)
    log.info("Added new import location: %s", location.directory)
    tasks.add_task(load_from_directory, location=location)
    return location

@app.get("/locations/{location_id}")
async def get_location(location_id: int, session: SessionDep) -> ImageLocation:
    """
    Retrieves a specific import location by its ID.
    
    Args:
        location_id (int): The ID of the import location.
    
    Returns:
        ImageLocation: The requested import location.
    """
    location = session.get(ImageLocation, location_id)
    if not location:
        raise HTTPException(status_code=404, detail=f"Location with ID {location_id} not found.")
    return location

@app.delete("/locations/{location_id}")
async def delete_location(location_id: int, session: SessionDep) -> None:
    """
    Deletes a specific import location by its ID.
    
    Args:
        location_id (int): The ID of the import location to delete.
    """
    location = session.get(ImageLocation, location_id)
    if not location:
        raise HTTPException(status_code=404, detail=f"Location with ID {location_id} not found.")
    session.delete(location)
    session.commit()

@app.get("/images")
async def get_images(session: SessionDep, limit: int=10, offset: int=0) -> list[Image]:
    """
    Retrieves all images from the database.
    
    Returns:
        list: A list of images.
    """
    images = session.exec(select(Image).limit(limit).offset(offset)).all()
    return images       