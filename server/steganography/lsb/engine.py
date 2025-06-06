from server.steganography.content_wrapper.wrapper import wrap_lsb, get_lsb_token_info, unwrap, get_max_unwapped_length
from server.steganography.image_utils import image_to_bytes
from server.steganography.lsb.lsb_image import *


def lsb_embed(source_image_bytes: bytes, message: bytes, key: str, ecc_block_size: int = 255,
              ecc_symbol_num: int = 16, num_of_sacrificed_bits: int = 2, check_capacity=True) -> tuple[bytes, bytes]:
    message, token = wrap_lsb(message, key.encode(), ecc_block_size, ecc_symbol_num, num_of_sacrificed_bits)
    img = LSBImage(source_image_bytes, num_of_sacrificed_bits)
    new_image = img.embed(message, check_capacity)
    return image_to_bytes(new_image), token


def lsb_extract(source_image_bytes: bytes, token: bytes) -> bytes:
    ((ecc_block_size, ecc_symbol_num), (verification_tag, nonce, update_header, key),
     seed, num_of_sacrificed_bits) = get_lsb_token_info(token)
    img = LSBImage(source_image_bytes, num_of_sacrificed_bits)
    wrapped = img.extract()
    return unwrap(wrapped, ecc_block_size, ecc_symbol_num, verification_tag, nonce, update_header, seed, key)


def lsb_calculate_max_capacity(source_image_bytes: bytes, ecc_block_size: int = 255, ecc_symbol_num: int = 16,
                               num_of_sacrificed_bits: int = 2) -> int:
    img = LSBImage(source_image_bytes, num_of_sacrificed_bits)
    total_available_bits = img.image.width*img.image.height*len(img.image.getbands())*num_of_sacrificed_bits
    iv_bit_len = img.iv_bit_len
    max_bit_embedding_input_length = total_available_bits - iv_bit_len
    return get_max_unwapped_length(max_bit_embedding_input_length, ecc_block_size, ecc_symbol_num)
