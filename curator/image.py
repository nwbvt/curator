import hashlib
import os
import exifread
from sqlmodel import Field, SQLModel, select

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

def list_images(session, limit, offset) -> list[Image]:
    images = session.exec(select(Image).limit(limit).offset(offset)).all()
    return images