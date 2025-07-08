import math
from random import choices
import numpy as np

from bpcs.core import calc_bpcs_complexity_coefficient


def get_prefix_length(block_area: int, min_alpha: float) -> int:
    """
    Calculates the length of the prefix for a given block area and minimum complexity coefficient.
    :param block_area: the total number of bits in a block
    :param min_alpha: the minimum complexity coefficient that the prefix should fulfill
    """
    # calibrated rho function
    return math.ceil(block_area * (1.4*min_alpha + 0.05))


def get_next_dynamically_prefixed_block(bits: list[bool], block_shape: tuple[int, int], min_alpha: float):
    """
    Builds a singular dynamically-prefixed block that contains a part of the given bits.
    :param bits: the bits
    :param block_shape: the shape of each bit plane block
    :param min_alpha: the minimum complexity coefficient that the prefix should fulfill
    :return: the built block, and the remaining bits
    """
    block_area = block_shape[0] * block_shape[1]
    prefix_length = get_prefix_length(block_area, min_alpha)
    data_length = block_area - prefix_length
    block_data, bits = bits[:data_length], bits[data_length:]

    if min_alpha == 0.0:
        return np.reshape(block_data, block_shape), bits

    while True:
        block = np.concatenate([choices([True, False], k=prefix_length), block_data])

        if len(block) < block_area:
            block = np.concatenate([block, choices([True, False], k=block_area - len(block))])

        block = np.reshape(block, block_shape)

        if calc_bpcs_complexity_coefficient(block) >= min_alpha:
            return block, bits


def bits_to_prefixed_blocks(bits: list[bool], block_shape: tuple[int, int], min_alpha: float) -> np.ndarray:
    """
    Construct prefixed blocks from data bits, where each block has a complexity coefficient of min_alpha or greater.
    :param bits: the array of data bits
    :param block_shape: the shape of each constructed block
    :param min_alpha: the minimum complexity coefficient of each block
    :return: the prefixed blocks constructed from the bits
    """
    blocks = []
    while len(bits) > 0:
        prefixed_block, bits = get_next_dynamically_prefixed_block(bits, block_shape, min_alpha)
        blocks.append(prefixed_block)

    return np.reshape(np.array(blocks), (len(blocks),) + block_shape)


def get_data_from_prefixed_blocks(blocks: np.ndarray, block_shape: tuple[int, int], alpha: float,
                                  data_bit_length: int) -> np.ndarray:
    """
    Parses the dynamically prefixed blocks, and extracts the data that they contain.
    :param blocks: the prefixed blocks we want to parse data from
    :param block_shape: the shape of each bit plane block given
    :param alpha: the minimum complexity coefficient that each block was prefixed to match
    :param data_bit_length: the length of the data we want to extract from the prefixed blocks in bits
    :return: an array of bools that represent the data we got from the prefixed blocks
    """
    data = np.array([], dtype=bool)
    block_area = block_shape[0] * block_shape[1]
    prefix_length = get_prefix_length(block_area, alpha)
    for block in blocks:
        block = np.reshape(block, (-1))
        data = np.append(data, block[prefix_length:])
    return data[:data_bit_length]
