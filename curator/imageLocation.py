import logging as log
import os
from fastapi import HTTPException
from sqlmodel import Field, SQLModel, col, select

from curator.db import db_session
from curator.image import IMAGE_FORMATS, Image, create_image

class ImageLocation(SQLModel, table=True):
    """Model representing an import location for images."""

    id: int | None = Field(default=None, primary_key=True)
    directory: str = Field(unique=True)


def image_files(d: str, existing: set[str] | None=None) -> list[str]:
    """
    Gets all image files in a directory and its subdirectories.

    Args:
        d (str): The path to the directory containing images.

    Returns:
        list: A list of image file paths.
    """
    if not os.path.exists(d):
        raise ValueError(f"The directory {d} does not exist.")
    if existing is None:
        with db_session() as session:
            existing = set(session.exec(select(Image.location).where(col(Image.location).startswith(d))).all())
    images = [os.path.join(d, f) for f in os.listdir(d) if f.lower().endswith(IMAGE_FORMATS)]
    images = [img for img in images if img not in existing]
    sub_directories = [os.path.join(d, d) for d in os.listdir(d) if os.path.isdir(os.path.join(d, d))]
    for sub_dir in sub_directories:
        images.extend(image_files(sub_dir, existing))
    return images


def load_from_directory(location):
    log.info("Loading images from %s", location.directory)
    files = image_files(location.directory)
    log.info("Found %d images in %s", len(files), location.directory)
    added=0
    with db_session() as session:
        for image_file in files:
            image = create_image(image_file)
            if session.exec(select(Image).where(Image.location == image_file)).first():
                log.debug("Image %s already exists in the database, skipping", image.location)
                continue
            session.add(image)
            added+=1
        session.commit()
    log.info("Added %d images to the database from %s", added, location.directory)


def load_images():
    """
    Loads images from the configured import locations and adds them to the database.
    """
    with db_session() as session:
        import_locations = session.exec(select(ImageLocation)).all()
    for location in import_locations:
        print(location)
        load_from_directory(location)


def list_locations(session):
    locations = session.exec(select(ImageLocation)).all()
    return locations

class LocationExists(Exception):
    """Exception raised when an import location already exists."""
    def __init__(self, directory):
        super().__init__(f"Import location '{directory}' already exists.")
        self.directory = directory

def create_image_location(directory, session, tasks):
    location = ImageLocation(directory=directory)
    if session.exec(select(ImageLocation).where(ImageLocation.directory == directory)).first():
        raise LocationExists(directory)
    session.add(location)
    session.commit()
    session.refresh(location)
    log.info("Added new import location: %s", location.directory)
    tasks.add_task(load_from_directory, location=location)
    return location


def get_image_location(location_id, session):
    location = session.get(ImageLocation, location_id)
    return location

class ImageLocationNotFound(Exception):
    """Exception raised when an image location is not found."""
    def __init__(self, location_id):
        super().__init__(f"Image location with ID {location_id} not found.")
        self.location_id = location_id

def delete_image_location(location_id, session):
    location = session.get(ImageLocation, location_id)
    if not location:
        raise ImageLocationNotFound(location_id)
    session.delete(location)
    session.commit()