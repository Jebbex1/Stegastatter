import io
import PIL
import PIL.Image
import numpy as np
from PIL import Image

from shared.communication_protocol.communication_errors import PacketContentsError


def open_image_from_bytes(image_bytes: bytes) -> PIL.Image.Image:
    try:
        return PIL.Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except PIL.UnidentifiedImageError:
        raise PacketContentsError("Expected image bytes, got otherwise")


def write_image(out_path: str, image: Image.Image) -> None:
    """
    Saves an image to a given path.
    :param out_path: the given path
    :param image: the image object to be saved
    """
    image.save(out_path, out_path.split('.')[-1])


def image_to_array(im: Image.Image) -> np.ndarray:
    """
    Converts a PIL image to a numpy array
    :param im: the image object to convert
    :return: the numpy array representing the image
    """
    return np.array(im)


def array_to_image(arr: np.ndarray) -> Image.Image:
    """
    Converts a numpy array to a PIL image
    :param arr: the numpy array representing the image
    :return: the converted PIL image
    """
    return Image.fromarray(np.uint8(arr))


def image_to_bytes(image: Image) -> bytes:
    image_bytes = io.BytesIO()
    image.save(image_bytes, format="PNG")
    return image_bytes.getvalue()
