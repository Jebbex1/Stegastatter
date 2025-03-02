import math
from random import choices
from typing import Generator, Any
import numpy as np


def bits_to_blocks(bit_list: list[bool], block_shape: tuple[int, int]) -> np.ndarray:
    """
    Converts a list of bits into blocks of a given shape.
    :param bit_list: list of bits  (every bit is a boolean value)
    :param block_shape: the shape of every wanted bit-plane block
    :return: a list of blocks in which any block is in the given shape
    """
    # calculate the remainder (if there is one)
    area = block_shape[0] * block_shape[1]
    rem = (len(bit_list) % area)
    length_missing = area - rem if rem else 0

    # correct the remainder
    bit_list += choices([True, False], k=length_missing)
    bit_list = np.array(bit_list)
    num_of_blocks = math.ceil(len(bit_list) / area)

    return np.resize(bit_list, [num_of_blocks, block_shape[0], block_shape[1]])


def bytes_to_blocks(message: bytes, block_shape: tuple[int, int]) -> np.ndarray:
    """
    Converts a bytestring in an array of blocks of a given shape that represent the bytestring.
    :param message: the bytestring to be converted
    :param block_shape: the wanted block shape
    :return: the bytestring in the form of blocks
    """
    def bits(st: bytes) -> Generator[bool, Any, None]:
        bytes_gen = (b for b in st)
        for b in bytes_gen:
            for i in reversed(range(8)):
                yield bool((b >> i) & True)

    bits_list = list(bits(message))  # get the list of bits from the message
    return bits_to_blocks(bits_list, block_shape)  # return structured blocks of the bits


def blocks_to_bits(blocks: np.ndarray) -> list[bool]:
    """
    Given a list of blocks of bits, convert the blocks into a large list of bits
    :param blocks: a list of bit blocks
    :return: the list of bits that the list of blocks contained, all in one dimension
    """
    blocks = [np.array(block).reshape(-1) for block in blocks]
    return np.hstack(blocks).flatten().tolist()
