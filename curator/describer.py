import ollama
from sqlmodel import select
import logging as log
from transformers import AutoProcessor, AutoModelForImageTextToText
from PIL import Image
import kagglehub

from curator import db, image, config

_PROMPT = """"
    You are an expert image describer. Your task is to provide a detailed description of the image.
    Describe the image in detail, including its content, colors, and any notable features.
    """

def describe_image(img: image.ImageData) -> str:
    """
    Uses Ollama to describe an image.

    Args:
        image_path (str): The path to the image file.

    Returns:
        str: The description of the image.
    """
    img_data = img.read_image()
    if config.settings.use_ollama:
        return describe_image_ollama(img_data)
    return describe_image_kaggle(img_data)
    
def describe_image_ollama(img_data: bytes) -> str:
    """
    Uses Ollama to describe an image.
    Args:
        img_data (bytes): The image data as bytes. 
    Returns:
        str: The description of the image.
    """
    model = config.settings.description_model
    try:
        response = ollama.generate(
            model=model,
            prompt=_PROMPT,
            images=[img_data],
        )
        return response.response
    except Exception as e:
        return f"Error describing image: {e}"

def get_model() -> tuple[AutoProcessor, AutoModelForImageTextToText]:
    """
    Loads the Hugging Face model for image description.
    
    Returns:
        tuple: A tuple containing the processor and model.
    """
    if 'model' in globals():
        return globals()['model']
    path = kagglehub.model_download(config.settings.description_model)
    processor = AutoProcessor.from_pretrained(path)
    model = AutoModelForImageTextToText.from_pretrained(path, torch_dtype='auto', device_map=config.settings.device)
    globals()['model'] = (processor, model)
    return processor, model

def describe_image_kaggle(img_data: bytes) -> str:
    """
    Uses a Kaggle model to describe an image.
    
    Args:
        img_data (bytes): The image data as bytes.
    
    Returns:
        str: The description of the image.
    """
    processor, model = get_model()
    prompt = "Image: <image_soft_token>\n" + _PROMPT
    log.info(f"Describing image with model {config.settings.description_model}")
    im = Image.frombytes('RGB', (64, 64), img_data)
    inputs = processor(images=im, text=prompt, return_tensors="pt").to(model.device)
    input_len = inputs.input_ids.shape[-1]
    outputs = model.generate(**inputs, max_new_tokens=100)[0][input_len:]
    decoded = processor.decode(outputs, skip_special_tokens=True)
    log.info(f"Got description {decoded}")
    return decoded

def run_describer():
    """
    Runs the image describer on all images without a discription.
    """
    chroma_coll = db.chroma_collection()
    with db.db_session() as session:
        images = session.exec(
            select(image.ImageData).where(image.ImageData.description.is_(None))
        ).all()
    log.info(f"Found {len(images)} images without description.")
    for img in images:
        description = describe_image(img)
        img.description = description
        with db.db_session() as session:
            image.set_image(img, session)
    log.info(f"Described {len(images)} images.")