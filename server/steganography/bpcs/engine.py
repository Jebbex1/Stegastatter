from server.steganography.bpcs.bpcs_image import BPCSImage
from server.steganography.bpcs.embed import get_message_blocks_from_bytes
from server.steganography.bpcs.capacity import calculate_maximum_capacity
from server.steganography.content_wrapper.wrapper import wrap_bpcs, get_bpcs_token_info, unwrap


def bpcs_embed(source_image_bytes: bytes, message: bytes, key: str, ecc_block_size: int = 255,
               ecc_symbol_num: int = 16, alpha: float = 0.3, check_capacity=True) -> tuple[bytes, bytes]:
    """
    Embeds message into the image at source_image_path, affecting blocks that have a
    complexity coefficient of alpha or greater, then saves the resulting image to output_file_path.
    """
    message, token = wrap_bpcs(message, key.encode(), ecc_block_size, ecc_symbol_num, alpha)
    img = BPCSImage(source_image_bytes, as_cgc=True)
    message_blocks, message_bit_length = get_message_blocks_from_bytes(message)
    arr = img.embed(message_blocks, message_bit_length, alpha, check_capacity)
    new_image_bytes = img.export(arr)
    return new_image_bytes, token


def bpcs_extract(source_image_bytes: bytes, token: bytes) -> bytes:
    """
    Extracts data from the image at source_image_path, and returns the data.
    """
    ((ecc_block_size, ecc_symbol_num), (verification_tag, nonce, update_header, key),
     seed, min_alpha) = get_bpcs_token_info(token)
    img = BPCSImage(source_image_bytes, as_cgc=True)
    wrapped = img.extract(min_alpha)
    return unwrap(wrapped, ecc_block_size, ecc_symbol_num, verification_tag, nonce, update_header, seed, key)


def bpcs_calculate_max_capacity(source_image_bytes: bytes, ecc_block_size: int = 255,
                                ecc_symbol_num: int = 16, alpha: float = 0.3) -> int:
    img = BPCSImage(source_image_bytes, as_cgc=True)
    image_shape = img.pixels.shape
    max_message_byte_length = calculate_maximum_capacity(img.pixels, image_shape, ecc_block_size, ecc_symbol_num, alpha)
    return max_message_byte_length
