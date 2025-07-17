import logging as log
from typing import Annotated
from fastapi import BackgroundTasks, Body, Depends, FastAPI, HTTPException, Response
from sqlmodel import Session
from curator import image, imageLocation, scheduler
from curator.db import create_db_and_tables, db_session

SessionDep = Annotated[Session, Depends(db_session)]

app = FastAPI()

@app.on_event("startup")
def on_startup():
    """
    Startup event handler to create the database and tables.
    """
    log.basicConfig(level=log.INFO)
    create_db_and_tables()
    scheduler.start_scheduler()

@app.get("/locations")
async def get_locations(session: SessionDep) -> list[imageLocation.ImageLocation]:
    """
    Retrieves all import locations from the database.
    
    Returns:
        list: A list of import locations.
    """
    locations = imageLocation.list_locations(session)
    return locations

@app.post("/locations", status_code=201)
async def add_location(directory: Annotated[str, Body(embed=True)],
                       session: SessionDep,
                       tasks: BackgroundTasks) -> imageLocation.ImageLocation:
    """
    Adds a new import location to the database.
    
    Args:
        location (ImageLocation): The import location to add.
    """
    try:
        location = imageLocation.create_image_location(directory, session, tasks)
        return location
    except imageLocation.LocationExists as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/locations/{location_id}")
async def get_location(location_id: int, session: SessionDep) -> imageLocation.ImageLocation:
    """
    Retrieves a specific import location by its ID.
    
    Args:
        location_id (int): The ID of the import location.
    
    Returns:
        ImageLocation: The requested import location.
    """
    location = imageLocation.get_image_location(location_id, session)
    if not location:
        raise HTTPException(status_code=404, detail=f"Location with ID {location_id} not found.")
    return location

@app.delete("/locations/{location_id}", status_code=204)
async def delete_location(location_id: int, session: SessionDep) -> None:
    """
    Deletes a specific import location by its ID.
    
    Args:
        location_id (int): The ID of the import location to delete.
    """
    try:
        imageLocation.delete_image_location(location_id, session)
    except imageLocation.ImageLocationNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/images", response_model=list[image.ImageMini])
async def get_images(session: SessionDep, limit: int=10, offset: int=0) -> list[image.ImageData]:
    """
    Retrieves all images from the database.
    
    Returns:
        list: A list of images.
    """
    images = image.list_images(session, limit, offset)
    return images 

@app.get("/images/{image_id}", response_model=image.ImageData)
async def get_image(image_id: int, session: SessionDep) -> image.ImageData:
    """
    Retrieves a specific image by its ID.
    
    Args:
        image_id (int): The ID of the image to retrieve.
    
    Returns:
        Image: The requested image.
    """
    img = image.get_image_data(image_id, session)
    if not img:
        raise HTTPException(status_code=404, detail=f"Image with ID {image_id} not found.")
    return img

class JPEGResponse(Response):
    """
    Custom response class for jpegs.
    """
    media_type = "image/jpeg"

    def render(self, content: bytes) -> bytes:
        log.info("Returning image with %d bytes", len(content))
        return content

@app.get("/images/{image_id}/jpeg")
async def get_jpeg(image_id: int, session: SessionDep) -> Response:
    """
    Retrieves the image file for a specific image.
    
    Args:
        image_id (int): The ID of the image.
    
    Returns:
        bytes: The image file content.
    """
    img = image.get_jpeg(image_id, session)
    if not img:
        raise HTTPException(status_code=404, detail=f"Image with ID {image_id} not found.")
    log.info("Returning image %d bytes", len(img))
    resp = Response(content=img, media_type="image/jpeg")
    return resp