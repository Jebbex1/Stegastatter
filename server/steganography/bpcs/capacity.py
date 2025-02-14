import math
import numpy as np

from bpcs.core import calc_bpcs_complexity_coefficient
from bpcs.dimension_computing import compute_all_block_indices


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
    bits_per_prefixed_block = block_area - math.ceil(alpha * block_area)

    iv_bit_length = len(bin(accepted_blocks_num)[2:]) + len(bin(block_area)[2:])
    conjugation_map_bit_length = math.ceil(message_bit_length / block_area)

    iv_block_length = math.ceil(iv_bit_length / bits_per_prefixed_block)
    conjugation_map_block_length = math.ceil(conjugation_map_bit_length / bits_per_prefixed_block)
    message_block_length = math.ceil(message_bit_length / block_area)

    return iv_block_length + conjugation_map_block_length + message_block_length


def calculate_if_fits(vessel_blocks: np.ndarray, image_shape: tuple[int, int, int, int], alpha: float,
                      message_bit_length: int) -> bool:
    """
    Calculates whether a message of arbitrary length can fit in an image together with all the decoding info blocks. If
    the total block length of the embedding payload is less than the number of accepted blocks, then the message fits.
    :param vessel_blocks: the images' vessel blocks
    :param image_shape: the shape of image
    :param alpha: the minimum complexity coefficient threshold
    :param message_bit_length: the bit length of the message
    :return: can a message of bit length message_bit_length fit into the image?
    """
    print("Calculating if embedding blocks will fit into the source image...")
    accepted_blocks_num = count_accepted_blocks(vessel_blocks, image_shape, (8, 8), alpha)
    embedding_blocks_num = calculate_embedding_blocks_num(accepted_blocks_num, (8, 8), alpha, message_bit_length)
    return accepted_blocks_num > embedding_blocks_num
