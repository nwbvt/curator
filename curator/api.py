import logging as log
from typing import Annotated
from fastapi import BackgroundTasks, Body, Depends, FastAPI, HTTPException
from sqlmodel import Session
from curator.imageLocation import ImageLocation, ImageLocationNotFound, LocationExists, create_image_location, delete_image_location, get_image_location, list_locations
from curator.image import Image, list_images
from curator.db import create_db_and_tables, db_session

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
    locations = list_locations(session)
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
    try:
        location = create_image_location(directory, session, tasks)
        return location
    except LocationExists as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/locations/{location_id}")
async def get_location(location_id: int, session: SessionDep) -> ImageLocation:
    """
    Retrieves a specific import location by its ID.
    
    Args:
        location_id (int): The ID of the import location.
    
    Returns:
        ImageLocation: The requested import location.
    """
    location = get_image_location(location_id, session)
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
    try:
        delete_image_location(location_id, session)
    except ImageLocationNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/images")
async def get_images(session: SessionDep, limit: int=10, offset: int=0) -> list[Image]:
    """
    Retrieves all images from the database.
    
    Returns:
        list: A list of images.
    """
    images = list_images(session, limit, offset)
    return images 

