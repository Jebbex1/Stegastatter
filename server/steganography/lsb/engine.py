import math

from server.steganography.content_wrapper.wrapper import wrap_lsb, get_lsb_token_info, unwrap
from server.steganography.image_utils import image_to_bytes
from server.steganography.lsb.lsb_image import *


def lsb_encode(source_image_bytes: bytes, message: bytes, key: str, ecc_block_size: int = 255,
               ecc_symbol_num: int = 16, num_of_sacrificed_bits: int = 2, check_capacity=True) -> tuple[bytes, bytes]:
    message, token = wrap_lsb(message, key.encode(), ecc_block_size, ecc_symbol_num, num_of_sacrificed_bits)
    img = LSBImage(source_image_bytes, num_of_sacrificed_bits)
    new_image = img.encode(message, check_capacity)
    return image_to_bytes(new_image), token


def lsb_decode(source_image_bytes: bytes, token: bytes) -> bytes:
    ((ecc_block_size, ecc_symbol_num),
     (verification_tag, nonce, update_header, key),
     num_of_sacrificed_bits) = get_lsb_token_info(token)
    img = LSBImage(source_image_bytes, num_of_sacrificed_bits)
    wrapped = img.decode()
    return unwrap(wrapped, ecc_block_size, ecc_symbol_num, verification_tag, nonce, update_header, key)


def lsb_check_if_fits_from_arbitrary(source_image_bytes: bytes, arbitrary_byte_length: int, ecc_block_size: int = 255,
                                     ecc_symbol_num: int = 16, num_of_sacrificed_bits: int = 2) -> bool:
    img = LSBImage(source_image_bytes, num_of_sacrificed_bits)
    wrapped_length = math.ceil(ecc_block_size * ((arbitrary_byte_length + 16) / (ecc_block_size - ecc_symbol_num)))
    return img.check_capacity(wrapped_length * 8)
