import hashlib
from io import BytesIO
import os
import exifread
import rawpy
from sqlmodel import Field, PrimaryKeyConstraint, SQLModel, Session, select
from PIL import Image

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

class ImageMini(SQLModel):
    """Model representing a minimal image representation for API responses."""
    id: int
    location: str
    format: str

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
    if image.format.lower() == 'nef':
        return process_nef(image)
    with open(image.location, 'rb') as f:
        return f.read()

def process_nef(image: ImageData) -> bytes:
    """
    Processes a NEF image file.
    
    Args:
        image (ImageData): The ImageData object representing the NEF image.
    
    Returns:
        Image: The processed image as a bytearray.
    """
    # Placeholder for NEF processing logic
    raw = rawpy.imread(image.location)
    rgb=raw.postprocess(use_camera_wb=True)
    im = Image.fromarray(rgb)
    bytes = BytesIO()
    im.save(bytes, format='JPEG')
    return bytes.getvalue()