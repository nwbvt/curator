import ollama
from sqlmodel import select
import logging as log

from curator import db, image, config

def describe_image(image: image.ImageData) -> str:
    """
    Uses Ollama to describe an image.

    Args:
        image_path (str): The path to the image file.

    Returns:
        str: The description of the image.
    """
    img = image.read_image(image)
    model = config.settings.description_model
    prompt = """"
    You are an expert image describer. Your task is to provide a detailed description of the image.
    Describe the image in detail, including its content, colors, and any notable features.
    """
    try:
        response = ollama.generate(
            model=model,
            prompt=prompt,
            images=[img],
        )
        return response.response
    except Exception as e:
        return f"Error describing image: {e}"

def run_describer():
    """
    Runs the image describer on all images without a discription.
    """
    with db.db_session() as session:
        images = session.exec(
            select(image.ImageData).where(image.ImageData.description.is_(None))
        ).all()
        for img in images:
            description = describe_image(img)
            img.description = description
            session.add(img)
        session.commit()
        log.info(f"Described {len(images)} images.")