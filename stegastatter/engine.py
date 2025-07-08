from bpcs.bpcs_image import BPCSImage
from bpcs.embed import get_message_blocks_from_bytes
from bpcs.capacity import calculate_maximum_capacity
from image_utils import image_to_bytes
from lsb.lsb_image import LSBImage
from content_wrapper.wrapper import wrap_bpcs, get_bpcs_token_info, wrap_lsb, get_lsb_token_info, \
    unwrap, get_max_unwapped_length
from steganalysis.bit_plane_slicing import slice_rgb_bit_planes
from steganalysis.get_diff import show_diff


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
    total_available_bits = img.image.width * img.image.height * len(img.image.getbands()) * num_of_sacrificed_bits
    iv_bit_len = img.iv_bit_len
    max_bit_embedding_input_length = total_available_bits - iv_bit_len
    return get_max_unwapped_length(max_bit_embedding_input_length, ecc_block_size, ecc_symbol_num)


def get_image_diffences(img1_bytes: bytes, img2_bytes: bytes, exact_diff: bool) -> tuple[tuple[int, int, int], bytes]:
    return show_diff(img1_bytes, img2_bytes, exact_diff)


def slice_image_bitplanes(image_bytes: bytes) -> list[tuple[str, bytes]]:
    bitplanes = []
    for name, bitplane_bytes in slice_rgb_bit_planes(image_bytes):
        bitplanes.append((name, bitplane_bytes))
    return bitplanes
