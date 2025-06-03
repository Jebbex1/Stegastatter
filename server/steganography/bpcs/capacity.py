import math
import numpy as np

from server.steganography.bpcs.core import calc_bpcs_complexity_coefficient
from server.steganography.bpcs.dimension_computing import compute_all_block_indices
from server.steganography.bpcs.dynamic_prefixing import get_prefix_length
from server.steganography.content_wrapper.wrapper import get_max_unwapped_length


def count_accepted_blocks(vessel_blocks: np.ndarray, image_shape: tuple[int, int, int, int],
                          block_shape: tuple[int, int], alpha: float) -> int:
    """
    Counts the number of accepted blocks. The threshold for being an accepted block is to have a complexity
    coefficient of alpha or greater.
    :param block_shape: the shape of each bit plane block
    :param image_shape: the shape of image
    :param vessel_blocks: the images' vessel blocks
    :param alpha: the minimum complexity coefficient threshold
    :return: the number of accepted blocks in the entire image
    """
    bit_plane_dims = compute_all_block_indices(image_shape, block_shape)
    noise_blocks_num = 0
    for bit_plane in bit_plane_dims:
        block = vessel_blocks[tuple(bit_plane)]  # get the current block to handle
        if calc_bpcs_complexity_coefficient(block) >= alpha:  # check if the block is valid for embedding data
            # if the block as a complexity coefficient that is sufficient for embedding data add 1 to the counter
            noise_blocks_num += 1
    return noise_blocks_num


def collect_accepted_blocks(vessel_blocks: np.ndarray, image_shape: tuple[int, int, int, int],
                            block_shape: tuple[int, int], alpha: float):
    bit_plane_dims = compute_all_block_indices(image_shape, block_shape)

    accepted_blocks = []
    for bit_plane in bit_plane_dims:
        block = vessel_blocks[tuple(bit_plane)]  # get the current block to handle
        if calc_bpcs_complexity_coefficient(block) >= alpha:
            accepted_blocks.append(tuple(bit_plane))
    return accepted_blocks


def calculate_embedding_blocks_num(accepted_blocks_num: int, block_shape: tuple[int, int], alpha: float,
                                   message_bit_length: int) -> int:
    """
    Calculates the number of blocks we need to modify to embed all the given data.
    :param accepted_blocks_num: the number of accepted blocks in the image
    :param block_shape: the shape of each bit plane block
    :param alpha: the minimum complexity coefficient threshold
    :param message_bit_length: the bit length of the message
    :return: the number of total block length of the embedding payload
    """
    block_area = block_shape[0] * block_shape[1]
    bits_per_prefixed_block = block_area - get_prefix_length(block_area, alpha)

    iv_bit_length = len(bin(accepted_blocks_num)[2:]) + len(bin(block_area)[2:])
    conjugation_map_bit_length = math.ceil(message_bit_length / block_area)

    iv_block_length = math.ceil(iv_bit_length / bits_per_prefixed_block)
    conjugation_map_block_length = math.ceil(conjugation_map_bit_length / bits_per_prefixed_block)
    message_block_length = math.ceil(message_bit_length / block_area)

    return iv_block_length + conjugation_map_block_length + message_block_length


def calculate_maximum_capacity(vessel_blocks: np.ndarray, image_shape: tuple[int, int, int, int],
                               ecc_block_size: int, ecc_symbol_num: int, alpha: float) -> int:
    block_shape_length = 8
    accepted_blocks_num = count_accepted_blocks(vessel_blocks, image_shape,
                                                (block_shape_length, block_shape_length), alpha)
    bits_per_prefixed_block = block_shape_length ** 2 - get_prefix_length(block_shape_length ** 2, alpha)
    iv_bit_length = math.ceil(math.log2(accepted_blocks_num)) + math.ceil(math.log2(block_shape_length ** 2))

    max_bit_embedding_input_length = math.floor(
        ((block_shape_length ** 2) * ((bits_per_prefixed_block * (accepted_blocks_num - 3)) - (iv_bit_length + 1)))
        /
        (bits_per_prefixed_block + 1)
    )

    return get_max_unwapped_length(max_bit_embedding_input_length, ecc_block_size, ecc_symbol_num)
