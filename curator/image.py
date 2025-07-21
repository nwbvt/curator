import hashlib
from io import BytesIO
import os
import exifread
from pydantic import BaseModel, computed_field
import rawpy
from sqlmodel import Field, SQLModel, Session, select
from PIL import Image

from curator import db

class ImageData(SQLModel, table=True):
    __tablename__ = 'image'
    """Model representing an image."""
    id: int | None = Field(default=None, primary_key=True)
    location: str = Field(unique=True)
    hash: str = Field(index=True, max_length=31)
    format: str = Field(max_length=3)
    description: str | None = None
    author: str | None = None
    camera: str | None = None
    orientation: int = Field(default=1),
    x_resolution: float | None = None
    y_resolution: float | None = None
    date_taken: str | None = None
    exposure_time: float | None = None
    f_number: float | None = None
    iso: int | None = None
    focal_length: float | None = None

    def read_image(self) -> bytes:
        """ Reads the image file and returns its content as bytes.
        Args:
            image (ImageData): The ImageData object representing the image.
        Returns:
            bytes: The content of the image file.
        """
        if self.format.lower() == 'nef':
            return self.process_nef()
        with open(self.location, 'rb') as f:
            return f.read()

    def process_nef(self) -> bytes:
        """
        Processes a NEF image file.
        
        Args:
            image (ImageData): The ImageData object representing the NEF image.
        
        Returns:
            Image: The processed image as a bytearray.
        """
        # Placeholder for NEF processing logic
        raw = rawpy.imread(self.location)
        rgb=raw.postprocess(use_camera_wb=True)
        im = Image.fromarray(rgb)
        bytes = BytesIO()
        im.save(bytes, format='JPEG')
        return bytes.getvalue()


class ImageMini(BaseModel):
    """Model representing a minimal image representation for API responses."""
    id: int

    @computed_field
    @property
    def url(self) -> str:
        """
        Returns the URL to access the image.
        
        Returns:
            str: The URL to access the image.
        """
        return f"/images/{self.id}"

    @computed_field
    @property
    def jpeg_url(self) -> str:
        """
        Returns the URL to access the JPEG version of the image.
        
        Returns:
            str: The URL to access the JPEG version of the image.
        """
        return f"/images/{self.id}/jpeg"

def exifValue(vals: dict, tag: str, default=None) -> str | float | int | None:
    """Extracts the value from an EXIF tag."""
    if tag in vals:
        exifValue = vals[tag]
        v = exifValue.values
        if isinstance(v, list):
            v = v[0]
        if exifValue.field_type.value == 5:
            return v.num
        return v
    return default

def create_image(image_file) -> ImageData:
    """
    Creates an Image object from a file, extracting metadata using EXIF.
    """
    with open(image_file, 'rb') as f:
        bytes = f.read()
        hash = hashlib.md5(bytes).hexdigest()
        exif = exifread.process_file(f, details=False)
    format = os.path.splitext(image_file)[1][1:]
    image = ImageData(location=image_file,
                  hash=hash,
                  format=format,
                  author=exifValue(exif, 'Image Artist'),
                  camera=exifValue(exif, 'Image Model'),
                  orientation=exifValue(exif, 'Image Orientation', 1),
                  x_resolution=exifValue(exif, 'Image XResolution'),
                  y_resolution=exifValue(exif, 'Image YResolution'),
                  date_taken=exifValue(exif, 'EXIF DateTimeOriginal'),
                  exposure_time=exifValue(exif, 'EXIF ExposureTime'),
                  f_number=exifValue(exif, 'EXIF FNumber'),
                  iso=exifValue(exif, 'EXIF ISOSpeedRatings'),
                  focal_length=exifValue(exif, 'EXIF FocalLength'))
    return image


IMAGE_FORMATS = ('.jpg', '.jpeg', '.nef')

def list_images(session: Session, limit: int, offset: int) -> list[ImageData]:
    """"
    Lists images from the database with pagination.
    
    Args:
        session (Session): The database session.
        limit (int): The maximum number of images to return.
        offset (int): The number of images to skip before starting to collect the result set.
    Returns:
        list[Image]: A list of Image objects.
    """
    images = session.exec(select(ImageData).limit(limit).offset(offset)).all()
    return images

def get_image_data(image_id: int, session: Session) -> ImageData | None:
    """
    Retrieves an image by its ID.
    
    Args:
        image_id (int): The ID of the image to retrieve.
        session (Session): The database session.
    
    Returns:
        Image | None: The requested image or None if not found.
    """
    return session.get(ImageData, image_id)

def get_jpeg(image_id: int, session: Session) -> bytes | None:
    """
    Retrieves an image by its ID.
    
    Args:
        image_id (int): The ID of the image to retrieve.
        session (Session): The database session.
    
    Returns:
        bytearray | None: The image data as a bytearray or None if not found.
    """
    image = session.get(ImageData, image_id)
    if not image:
        return None
    return image.read_image()

def search_images(query: str, session: Session, num_results: int=10) -> list[ImageData]:
    """
    Searches for images based on a query string.
    
    Args:
        query (str): The search query.
        session (Session): The database session.
        num_results (int): The maximum number of results to return.
    
    Returns:
        list[Image]: A list of images matching the search query.
    """
    chroma_coll = db.chroma_collection()
    matches = chroma_coll.query(
        query_texts=[query],
        include=[],
        n_results=num_results,
    )
    image_ids = [int(id) for id in matches['ids'][0]]
    images = session.exec(
        select(ImageData).where(ImageData.id.in_(image_ids))
    ).all()
    return images

METADATA_FIELDS = [
    'author', 'camera', 'date_taken', 'exposure_time', 'f_number', 'iso', 'focal_length'
]

def set_image(image: ImageData, session: Session) -> None:
    """
    Adds or updates an image in the database.
    
    Args:
        image (ImageData): The ImageData object to add or update.
        session (Session): The database session.
    """
    session.add(image)
    image_model = image.model_dump()
    session.commit()
    chroma_coll = db.chroma_collection()
    metadata = {prop: image_model[prop] for prop in image_model if prop in METADATA_FIELDS}
    chroma_coll.add(
                documents=[image.description],
                metadatas=[metadata],
                ids=[str(image.id)],
            )