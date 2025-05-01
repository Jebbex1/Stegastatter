import logging
import math
import multiprocessing
import sys
from random import choices
import numpy as np

from server.steganography.bpcs.core import calc_bpcs_complexity_coefficient


def get_prefix_length(block_area: int, alpha: float) -> int:
    """
    Calculates the length of the prefix for a given block area and minimum complexity coefficient.
    :param block_area: the total number of bits in a block
    :param alpha: the minimum complexity coefficient that the prefix should fulfill
    """
    return math.ceil(1.625 * alpha * block_area)  # rho function


def bit_array_to_int(bit_array: np.ndarray) -> int:
    """
    Given a bit array, convert it into a decimal integer and return it.
    :param bit_array: an array of bits (bools)
    :return: the decimal integer representation of the bit array value
    """
    return int("".join([str(int(i)) for i in bit_array.tolist()]), 2)


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
    :return:
    """
    blocks = []
    while len(bits) > 0:
        prefixed_block, bits = get_next_dynamically_prefixed_block(bits, block_shape, min_alpha)
        blocks.append(prefixed_block)

    return np.reshape(np.array(blocks), (len(blocks),) + block_shape)


def build_message_length_iv(number_of_accepted_blocks: int, block_shape: tuple[int, int],
                            message_bit_length: int) -> np.ndarray:
    """
    Builds an initialization vector that contains the message block length.
    :param number_of_accepted_blocks: the number of accepted blocks
    :param block_shape: the shape of each bit plane block in the image
    :param message_bit_length: the length of the message in bits
    :return: the initialization vector that contains the message block length, sized to a static length for that image
    with a specific block shape and complexity coefficient.
    """
    message_block_length = math.ceil(message_bit_length / (block_shape[0] * block_shape[1]))
    iv = str.zfill(bin(message_block_length)[2:], len(bin(number_of_accepted_blocks)[2:]))
    return np.array([bool(int(i)) for i in iv])


def build_message_remnant_iv(block_shape: tuple[int, int], message_bit_length: int) -> np.ndarray:
    """
    Builds an initialization vector that contains the number of bits in the last message block that belong to the
    message and aren't just filler bits.
    :param block_shape: the shape of each bit plane block in the image
    :param message_bit_length: the length of the message in bits
    :return: initialization vector that contains the number of bits in the last message block that belong to the
    message and aren't just filler bits, sized to a constant length of the specific block shape.
    """
    block_area = block_shape[0] * block_shape[1]
    message_remnant_bits_num = message_bit_length % block_area
    if message_remnant_bits_num == 0:
        message_remnant_bits_num = block_area
    iv = str.zfill(str(bin(message_remnant_bits_num)[2:]), len(bin(block_area)[2:]))
    return np.array([bool(int(i)) for i in iv])


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


def build_iv_blocks(number_of_accepted_blocks: int, block_shape: tuple[int, int],
                    alpha: float, message_bit_length: int) -> np.ndarray:
    """
    Builds the initialization vector blocks given the needed parameters. Each initialization vector has a constant
    length that depends on the number of accepted blocks, the block shape, and the minimum complexity coefficient.
    :param number_of_accepted_blocks: the number of bit plane blocks in the entire image that have a complexity
    coefficient of alpha or greater
    :param block_shape: the shape of each block in the image, and the wanted shape of each iv block
    :param alpha: the minimum complexity coefficient that each iv block needs to be prefixed to match
    :param message_bit_length: the length of the message in bits
    :return: an array of the initialization vector blocks
    """
    message_length_iv = build_message_length_iv(number_of_accepted_blocks, block_shape, message_bit_length)
    message_remnant_iv = build_message_remnant_iv(block_shape, message_bit_length)
    iv_bits = np.append(message_length_iv, message_remnant_iv)
    return bits_to_prefixed_blocks(iv_bits.tolist(), block_shape, min_alpha=alpha)


def build_conjugation_blocks(conjugation_map: list[bool], block_shape: tuple[int, int], alpha: float) -> np.ndarray:
    """
    Builds the conjugation blocks.
    :param conjugation_map: a list of bits that represent the conjugation map of the embedded message
    :param block_shape: the shape of each bit plane block in the image
    :param alpha: the minimum complexity coefficient that each iv block needs to be prefixed to match
    :return: the conjugation map blocks, prefixed to have a complexity coefficient of alpha or greater
    """
    return bits_to_prefixed_blocks(conjugation_map, block_shape, alpha)


def slice_iv_from_accepted_blocks(blocks: np.ndarray, block_shape: tuple[int, int],
                                  alpha: float) -> tuple[tuple[int, int], np.ndarray]:
    """
    Finds, separates, and extracts data from the initialization vector blocks in an array of image's bit plane blocks,
    using the constant length of the iv for every image and its parameters. This function assumes the relevant blocks
    begin at index = 0 of the given array of blocks.
    :param blocks: the images' bit plane blocks that have a complexity coefficient of alpha or more
    :param block_shape: the shape of each bit plane block in the image
    :param alpha: the minimum complexity coefficient of each block that was given
    :return: the data from the initialization vector blocks, and the remaining block in the form:
    (message_block_length, message_remnant_bits), remaining blocks
    """
    # calculate what's the length of the iv in blocks, using the constant length for each iv part
    block_area = block_shape[0] * block_shape[1]
    iv_bit_length = len(bin(len(blocks))[2:]) + len(bin(block_area)[2:])
    available_bits_per_block = block_area - get_prefix_length(block_area, alpha)
    iv_block_length = math.ceil(iv_bit_length / available_bits_per_block)

    # separate the iv blocks from the rest of the blocks, and extract the data from the iv blocks
    iv_blocks, remaining_blocks = blocks[:iv_block_length], blocks[iv_block_length:]
    iv_bits = get_data_from_prefixed_blocks(iv_blocks, block_shape, alpha, iv_bit_length)
    message_length_iv_len = len(bin(len(blocks))[2:])
    message_length_iv, message_remnant_iv = iv_bits[:message_length_iv_len], iv_bits[message_length_iv_len:]
    return (bit_array_to_int(message_length_iv), bit_array_to_int(message_remnant_iv)), remaining_blocks


def slice_conj_blocks_from_accepted_blocks(blocks: np.ndarray, block_shape: tuple[int, int], alpha: float,
                                           embedded_message_blocks_num: int) -> tuple[list[bool], np.ndarray]:
    """
    Extracts the conjugation map from the images' accepted blocks.
    :param blocks: the images' bit plane blocks that have a complexity coefficient of alpha or more
    :param alpha: the minimum complexity coefficient of each block that was given
    :param block_shape: the shape of each bit plane block in the image
    :param embedded_message_blocks_num: the number of embedded message blocks in the image, this is also the length of
    the conjugation map in bits.
    :return: the conjugation map blocks, and the remaining blocks in the form: (map, remaining blocks)
    """
    conj_map_bit_length = embedded_message_blocks_num
    block_area = block_shape[0] * block_shape[1]

    conj_map_block_length = math.ceil(conj_map_bit_length / (block_area - get_prefix_length(block_area, alpha)))

    conj_blocks, remaining = blocks[:conj_map_block_length], blocks[conj_map_block_length:]

    return get_data_from_prefixed_blocks(conj_blocks, block_shape, alpha, conj_map_bit_length).tolist(), remaining
