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

class ImageDescription(SQLModel, table=True):
    """Model representing an image description."""
    __table_args__ = (PrimaryKeyConstraint('image_id', 'author', name='uq_image_author'),)
    image_id: int = Field(foreign_key='image.id')
    description: str = Field(max_length=255)
    author: str | None = None


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

def get_image_descriptions(image_id: int, session: Session) -> list[ImageDescription]:
    """
    Retrieves all descriptions for a specific image.
    
    Args:
        image_id (int): The ID of the image.
        session (Session): The database session.
    
    Returns:
        list[ImageDescription]: A list of ImageDescription objects.
    """
    return session.exec(select(ImageDescription).where(ImageDescription.image_id == image_id)).all()

def get_image_description(image_id: int, author: str | None, session: Session) -> ImageDescription | None:
    """
    Retrieves a specific description for an image by author.
    
    Args:
        image_id (int): The ID of the image.
        author (str | None): The author of the description.
        session (Session): The database session.
    
    Returns:
        ImageDescription | None: The requested ImageDescription or None if not found.
    """
    return session.exec(
        select(ImageDescription).where(
            ImageDescription.image_id == image_id,
            ImageDescription.author == author
        )
    ).first()

def add_image_description(image_id: int, description: str,
                          author: str | None, session: Session):
    """
    Adds a description to an image.
    
    Args:
        image_id (int): The ID of the image.
        description (str): The description text.
        author (str | None): The author of the description.
        session (Session): The database session.
    
    Returns:
        ImageDescription: The created ImageDescription object.
    """
    image_desc = session.exec(
        select(ImageDescription).where(
            ImageDescription.image_id == image_id,
            ImageDescription.author == author
        )
    ).first()
    if image_desc:
        image_desc.description = description
    else:
        image_desc = ImageDescription(image_id=image_id, description=description, author=author)
    session.add(image_desc)
    session.commit()
    return image_desc

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