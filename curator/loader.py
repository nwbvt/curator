import hashlib
from logging import log
import os
from sqlmodel import Session, select

from curator.data_model import Image, ImageLocation, db_session

IMAGE_FORMATS = ('.png', '.jpg', '.jpeg', '.gif', '.nef')

def image_files(dir: str) -> list[str]:
    """
    Gets all image files in a directory and its subdirectories.
    
    Args:
        dir (str): The path to the directory containing images.
        
    Returns:
        list: A list of image file paths.
    """
    if not os.path.exists(dir):
        raise ValueError(f"The directory {dir} does not exist.")
    
    images = [os.path.join(dir, f) for f in os.listdir(dir) if f.lower().endswith(IMAGE_FORMATS)]
    sub_directories = [os.path.join(dir, d) for d in os.listdir(dir) if os.path.isdir(os.path.join(dir, d))]
    for sub_dir in sub_directories:
        images.extend(image_files(sub_dir))
    return images

def load_images():
    """
    Loads images from the configured import locations and adds them to the database.
    """
    with db_session() as session:
        import_locations = session.exec(select(ImageLocation)).all()
        for location in import_locations:
            print(location)
            images = image_files(location.directory)
            for image in images:
                with open(image, 'rb') as f:
                    bytes = f.read()
                    hash = hashlib.md5(bytes).hexdigest()
                format = os.path.splitext(image)[1][1:]
                image = Image(
                    location=image,
                    hash=hash,
                    format=format
                )
                session.add(image)
        session.commit()