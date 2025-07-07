import hashlib
import os
import exifread
from sqlmodel import Field, SQLModel, Session, UniqueConstraint, select

class Image(SQLModel, table=True):
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
    __table_args__ = (UniqueConstraint('image_id', 'author', name='uq_image_author'),)
    id: int | None = Field(default=None, primary_key=True)
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

def create_image(image_file) -> Image:
    """
    Creates an Image object from a file, extracting metadata using EXIF.
    """
    with open(image_file, 'rb') as f:
        bytes = f.read()
        hash = hashlib.md5(bytes).hexdigest()
        exif = exifread.process_file(f, details=False)
    format = os.path.splitext(image_file)[1][1:]
    image = Image(location=image_file,
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


IMAGE_FORMATS = ('.png', '.jpg', '.jpeg', '.gif', '.nef')

def list_images(session: Session, limit: int, offset: int) -> list[Image]:
    """"
    Lists images from the database with pagination.
    
    Args:
        session (Session): The database session.
        limit (int): The maximum number of images to return.
        offset (int): The number of images to skip before starting to collect the result set.
    Returns:
        list[Image]: A list of Image objects.
    """
    images = session.exec(select(Image).limit(limit).offset(offset)).all()
    return images

def get_image(image_id: int, session: Session) -> Image | None:
    """
    Retrieves an image by its ID.
    
    Args:
        image_id (int): The ID of the image to retrieve.
        session (Session): The database session.
    
    Returns:
        Image | None: The requested image or None if not found.
    """
    return session.get(Image, image_id)

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