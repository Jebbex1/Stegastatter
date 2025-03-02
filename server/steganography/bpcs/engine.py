import math

from server.steganography.bpcs.bpcs_image import BPCSImage
from server.steganography.bpcs.encode import get_message_blocks_from_bytes
from server.steganography.bpcs.capacity import calculate_if_fits
from server.steganography.content_wrapper.wrapper import wrap_bpcs, get_bpcs_token_info, unwrap


def encode(source_image_bytes: bytes, message: bytes, key: str, ecc_block_size: int = 255,
           ecc_symbol_num: int = 16, alpha: float = 0.3, check_capacity=True) -> tuple[bytes, bytes]:
    """
    Encodes message into the image at source_image_path, affecting blocks that have a
    complexity coefficient of alpha or greater, then saves the resulting image to output_file_path.
    """
    message, token = wrap_bpcs(message, key.encode(), ecc_block_size, ecc_symbol_num, alpha)
    img = BPCSImage(source_image_bytes, as_cgc=True)
    message_blocks, message_bit_length = get_message_blocks_from_bytes(message)
    arr = img.encode(message_blocks, message_bit_length, alpha, check_capacity)
    new_image_bytes = img.export(arr)
    return new_image_bytes, token


def decode(source_image_bytes: bytes, token: bytes) -> bytes:
    """
    Decodes data from the image at source_image_path, and returns the data.
    """
    (ecc_block_size, ecc_symbol_num), (verification_tag, nonce, update_header, key), alpha = get_bpcs_token_info(token)
    img = BPCSImage(source_image_bytes, as_cgc=True)
    wrapped = img.decode(alpha)
    return unwrap(wrapped, ecc_block_size, ecc_symbol_num, verification_tag, nonce, update_header, key)


def check_if_fits_from_arbitrary(source_image_bytes: bytes, arbitrary_byte_length: int, ecc_block_size: int = 255,
                                 ecc_symbol_num: int = 16, alpha: float = 0.3) -> bool:
    """
    Checks if a message with an arbitrary bit length can fit in the image at source_image_path.
    """
    img = BPCSImage(source_image_bytes, as_cgc=True)
    image_shape = img.pixels.shape
    wrapped_length = math.ceil(ecc_block_size * ((arbitrary_byte_length + 16) / (ecc_block_size - ecc_symbol_num)))
    return calculate_if_fits(img.pixels, image_shape, alpha, wrapped_length * 8)
