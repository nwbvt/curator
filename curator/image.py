import hashlib
import os
from sqlmodel import Field, SQLModel

class Image(SQLModel, table=True):
    """Model representing an image."""

    id: int | None = Field(default=None, primary_key=True)
    location: str = Field(unique=True)
    hash: str = Field(index=True, max_length=31)
    description: str | None = None
    format: str = Field(max_length=3)


def create_image(image_file):
    with open(image_file, 'rb') as f:
        bytes = f.read()
        hash = hashlib.md5(bytes).hexdigest()
    format = os.path.splitext(image_file)[1][1:]
    image = Image(location=image_file,
                  hash=hash,
                  format=format)

    return image


IMAGE_FORMATS = ('.png', '.jpg', '.jpeg', '.gif', '.nef')