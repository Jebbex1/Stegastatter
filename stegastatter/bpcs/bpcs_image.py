import multiprocessing

import numpy as np

from bpcs.bit_plane import BitPlane
from bpcs.extract import extract_message_from_vessel
from bpcs.embed import embed_message_in_vessel
from image_utils import open_image_from_bytes, image_to_array, array_to_image, image_to_bytes


class BPCSImage:
    """
    The class that manages the reading, writing, embedding, and extracting data in an PIL image object using BPCS
    steganography.
    """
    def __init__(self, image_bytes: bytes, as_cgc: bool):
        """
        Initializes a new instance of the BPCSImage class.
        :param as_cgc: should the image be read in CGC instead of PBC?
        """
        update_logger = multiprocessing.get_logger()
        self.image_bytes = image_bytes
        self.as_gray = as_cgc
        self.pixels = self.read()
        update_logger.info(f"Loaded image as array with shape {self.pixels.shape}")

    def read(self) -> np.ndarray:
        img = open_image_from_bytes(self.image_bytes)
        pixels = image_to_array(img)
        pixels = BitPlane(pixels, self.as_gray).slice()
        return pixels

    def export(self, pixels: np.ndarray) -> bytes:
        update_logger = multiprocessing.get_logger()
        pixels = BitPlane(pixels, self.as_gray).stack()
        img = array_to_image(pixels)
        update_logger.info("Loaded new bit plane blocks as an image!")
        return image_to_bytes(img)

    def embed(self, message_blocks: np.ndarray, message_bit_length: int, alpha: float,
              check_capacity: bool) -> np.ndarray:
        """
        Embeds the given message blocks into the pixels attribute.
        :param message_blocks: the blocks that describe the message we want to embed
        :param message_bit_length: the length of the message in bits
        :param alpha: the complexity coefficient threshold of the BPCS algorithm
        :param check_capacity: should the program check the images' capacity before starting to embed the message blocks
        :return: the resulting pixels after embedding
        """

        new_arr = np.array(self.pixels, copy=True)
        embedded_arr = embed_message_in_vessel(new_arr, alpha, message_blocks, message_bit_length, (8, 8), check_capacity)
        return embedded_arr

    def extract(self, alpha: float) -> bytes:
        """
        Extracts the message hidden in the pixels attribute.
        :param alpha: the complexity coefficient threshold of the BPCS algorithm
        :return: the extracted message bytes
        """
        return extract_message_from_vessel(self.pixels, alpha, (8, 8))
