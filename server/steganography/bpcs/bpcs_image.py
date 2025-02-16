import io
import logging
import threading

import numpy as np
from PIL import Image

from server.steganography.bpcs.bit_plane import BitPlane
from server.steganography.bpcs.decode import read_message_from_vessel
from server.steganography.bpcs.encode import embed_message_in_vessel
from server.steganography.steganography_errors import SteganographyError
from shared.communication_protocol.communication_errors import PacketContentsError
from server.steganography.image_utils import open_image_from_bytes


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


class BPCSImage:
    """
    The class that manages the reading, writing, encoding, and decoding data in an PIL image object using BPCS
    steganography.
    """
    def __init__(self, image_bytes: bytes, as_cgc: bool):
        """
        Initializes a new instance of the BPCSImage class.
        :param as_cgc: should the image be read in CGC instead of PBC?
        """
        update_logger = logging.getLogger(str(threading.get_ident()))
        self.image_bytes = image_bytes
        self.as_gray = as_cgc
        self.num_of_bits_per_layer = 8
        self.pixels = self.read()
        update_logger.info(f"Loaded image as array with shape {self.pixels.shape}")

    def read(self) -> np.ndarray:
        """
        Loads the image at the image path, converts it to an array describing the pixels, then converts it into a bit
        plane.
        :return: bit planes that describe the images pixels
        """
        img = open_image_from_bytes(self.image_bytes)
        pixels = image_to_array(img)
        pixels = BitPlane(pixels, self.as_gray).slice(self.num_of_bits_per_layer)
        return pixels

    def export(self, pixels: np.ndarray) -> bytes:
        """
        Writes the given image pixels to the given path.
        :param pixels: the pixels that describe the image we want to write
        """
        update_logger = logging.getLogger(str(threading.get_ident()))
        pixels = BitPlane(pixels, self.as_gray).stack()
        img = array_to_image(pixels)
        update_logger.info("Loaded new bit plane blocks as an image!")
        image_bytes = io.BytesIO()
        img.save(image_bytes, format="PNG")
        return image_bytes.getvalue()

    def encode(self, message_blocks: np.ndarray, message_bit_length: int, alpha: float,
               check_capacity: bool) -> np.ndarray:
        """
        Encodes the given message blocks into the pixels attribute.
        :param message_blocks: the blocks that describe the message we want to encode
        :param message_bit_length: the length of the message in bits
        :param alpha: the complexity coefficient threshold of the BPCS algorithm
        :param check_capacity: should the program check the images' capacity before starting to embed the message blocks
        :return: the resulting pixels after encoding
        """
        new_arr = np.array(self.pixels, copy=True)
        encoded_arr = embed_message_in_vessel(new_arr, alpha, message_blocks, message_bit_length, (8, 8), check_capacity)
        return encoded_arr

    def decode(self, alpha: float) -> bytes:
        """
        Decodes the message hidden in the pixels attribute.
        :param alpha: the complexity coefficient threshold of the BPCS algorithm
        :return: the decoded message bytes
        """
        return read_message_from_vessel(self.pixels, alpha, (8, 8))
